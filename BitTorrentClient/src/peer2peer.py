import socket
import struct
import threading

"""
MADE BY SATYA PALADUGU
The Worker Thread.
Handles Handshake, Message Loop, Downloading, and Uploading.
"""

class PeerConnection(threading.Thread):
    def __init__(self, piece_manager, info_hash, peer_id, ip=None, port=None, sock=None):
        threading.Thread.__init__(self) 
        self.piece_manager = piece_manager 
        self.info_hash = info_hash
        self.peer_id = peer_id
        
        if sock:
            # Incoming (Server)
            self.sock = sock
            self.ip, self.port = sock.getpeername()
            self.connected = True
        else:
            # Outgoing (Client)
            self.sock = None
            self.ip = ip
            self.port = port
            self.connected = False

        self.timeout = 10
        self.am_choking = True       
        self.am_interested = False   
        self.peer_choking = True     
        self.peer_interested = False 
        self.bitfield = []           

    def run(self):
        if not self.connected:
            if not self.connect(): return
            
        if not self.perform_handshake():
            self.close()
            return
            
        self.start_listening()
        self.close()

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.ip, self.port))
            return True
        except: return False

    def recv_exact(self, n):
        data = b''
        while len(data) < n:
            try:
                packet = self.sock.recv(n - len(data))
                if not packet: return None 
                data += packet
            except: return None
        return data

    def perform_handshake(self):
        if not self.sock: return False
        pstr = b'BitTorrent protocol'
        handshake_msg = bytes([19]) + pstr + (b'\x00' * 8) + self.info_hash + self.peer_id
        
        try:
            self.sock.send(handshake_msg)
            response = self.recv_exact(68)
            if not response: return False
            if response[28:48] != self.info_hash: return False
            
            self.connected = True
            return True
        except: return False

    def start_listening(self):
        self.sock.settimeout(120) 
        while self.connected:
            try:
                # Read Length (4 bytes)
                length_data = self.recv_exact(4)
                if not length_data: break
                msg_length = struct.unpack('>I', length_data)[0]
                if msg_length == 0: continue # Keep-Alive

                # Read ID (1 byte)
                msg_id_data = self.recv_exact(1)
                if not msg_id_data: break
                msg_id = msg_id_data[0] 

                # Read Payload
                payload = self.recv_exact(msg_length - 1)
                if payload is None: break
                
                self.handle_message(msg_id, payload)
            except Exception:
                self.connected = False
                break

    def handle_message(self, msg_id, payload):
        if msg_id == 0:
            self.peer_choking = True
        elif msg_id == 1:
            self.peer_choking = False
            self.request_next_block()
        elif msg_id == 4:
            self.handle_have(payload)
        elif msg_id == 5:
            self.handle_bitfield(payload)
        elif msg_id == 6:
            self.handle_request(payload) # Seeding
        elif msg_id == 7:
            self.handle_piece_block(payload) # Downloading

    def handle_bitfield(self, payload):
        self.bitfield = []
        for byte in payload:
            for i in range(8):
                self.bitfield.append(((byte >> (7 - i)) & 1) == 1)
        if any(self.bitfield): self.send_interested()
        if not self.peer_choking: self.request_next_block()

    def handle_have(self, payload):
        piece_index = struct.unpack('>I', payload)[0]
        while len(self.bitfield) <= piece_index: self.bitfield.append(False)
        self.bitfield[piece_index] = True
        if not self.am_interested: self.send_interested()
        if not self.peer_choking: self.request_next_block()

    def send_interested(self):
        try:
            self.sock.send(struct.pack('>Ib', 1, 2))
            self.am_interested = True
        except: pass

    def handle_request(self, payload):
        """ Peer wants to download from us """
        if len(payload) < 12: return
        index, begin, length = struct.unpack('>III', payload)
        
        data = self.piece_manager.read_block(index, begin, length)
        if data:
            self.send_piece(index, begin, data)
            
    def send_piece(self, index, begin, block_data):
        payload = struct.pack('>II', index, begin) + block_data
        msg = struct.pack('>Ib', 9 + len(block_data), 7) + payload
        try: self.sock.send(msg)
        except: pass

    def request_next_block(self):
        if self.peer_choking: return
        request = self.piece_manager.get_next_request(self.bitfield)
        if request is None: return

        piece_index, block_offset, block_length = request
        payload = struct.pack('>III', piece_index, block_offset, block_length)
        msg = struct.pack('>Ib', 13, 6) + payload
        
        try: self.sock.send(msg)
        except: pass

    def handle_piece_block(self, payload):
        if len(payload) < 8: return
        piece_index = struct.unpack('>I', payload[:4])[0]
        begin = struct.unpack('>I', payload[4:8])[0]
        block_data = payload[8:]
        
        self.piece_manager.block_received(piece_index, begin, block_data)
        self.request_next_block()

    def close(self):
        if self.sock:
            self.sock.close()
            self.connected = False