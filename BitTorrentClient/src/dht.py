import socket
import struct
import threading
import time
import hashlib
import random
from collections import deque
from bencoding import bencodeDecode

"""
MADE BY SATYA PALADUGU
BEP 05: Distributed Hash Table (DHT) Node.
Handles UDP KRPC Protocol.
"""

class DHTNode(threading.Thread):
    def __init__(self, port, peer_id):
        threading.Thread.__init__(self)
        self.port = port
        self.node_id = hashlib.sha1(peer_id).digest() 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.port)) 
        self.running = False
        self.decoder = bencodeDecode()
        
        # Routing Table: List of (node_id, ip, port)
        self.nodes = [] 

    def run(self):
        self.running = True
        print(f"DHT Node Listening on UDP {self.port}")
        
        # Bootstrap on start
        self.bootstrap()
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(2048)
                self.handle_packet(data, addr)
            except:
                pass

    def handle_packet(self, data, addr):
        try:
            # Decode Bencoded dictionary
            msg = self.decoder.bencodeDecode(deque(data))
            if not msg: return

            msg_type = msg.get(b'y')
            
            if msg_type == b'q': # Query
                self.handle_query(msg, addr)
            elif msg_type == b'r': # Response
                self.handle_response(msg, addr)
                
        except Exception:
            pass

    def handle_query(self, msg, addr):
        query = msg.get(b'q')
        trans_id = msg.get(b't')
        
        if query == b'ping':
            # Reply with 'pong'
            self.send_response(addr, trans_id, {b'id': self.node_id})
            
        elif query == b'find_node':
            # Return up to 8 known nodes
            compact_nodes = self.pack_nodes(self.nodes[:8]) 
            self.send_response(addr, trans_id, {b'id': self.node_id, b'nodes': compact_nodes})

    def handle_response(self, msg, addr):
        # If we got a response, add them to our routing table
        r = msg.get(b'r')
        if r and b'id' in r:
            remote_id = r[b'id']
            self.add_node(remote_id, addr[0], addr[1])
            
        # If they sent us nodes (find_node response), add them too
        if r and b'nodes' in r:
            self.unpack_nodes(r[b'nodes'])

    def send_response(self, addr, trans_id, args):
        response = {
            b't': trans_id,
            b'y': b'r',
            b'r': args
        }
        try:
            encoded = self.bencode(response)
            self.sock.sendto(encoded, addr)
        except: pass

    def send_query(self, addr, query_type, args):
        trans_id = random.randbytes(2)
        msg = {
            b't': trans_id,
            b'y': b'q',
            b'q': query_type.encode('utf-8'),
            b'a': args
        }
        try:
            encoded = self.bencode(msg)
            self.sock.sendto(encoded, addr)
        except: pass

    def bootstrap(self):
        """ Connect to public bootstrap nodes """
        BOOTSTRAP_NODES = [
            ("router.bittorrent.com", 6881),
            ("dht.transmissionbt.com", 6881),
            ("router.utorrent.com", 6881)
        ]
        print("DHT: Bootstrapping...")
        for host, port in BOOTSTRAP_NODES:
            try:
                ip = socket.gethostbyname(host)
                self.send_query((ip, port), "find_node", {b'id': self.node_id, b'target': self.node_id})
            except:
                pass

    def add_node(self, node_id, ip, port):
        # Avoid duplicates
        for n in self.nodes:
            if n[0] == node_id: return
        self.nodes.append((node_id, ip, port))

    def pack_nodes(self, nodes):
        """Pack list of (id, ip, port) into compact binary string"""
        packed = b''
        for nid, ip, port in nodes:
            try:
                packed += nid
                packed += socket.inet_aton(ip)
                packed += struct.pack(">H", port)
            except: pass
        return packed

    def unpack_nodes(self, data):
        """Unpack compact binary string into nodes list"""
        length = len(data)
        for i in range(0, length, 26):
            if i + 26 > length: break
            nid = data[i:i+20]
            ip = socket.inet_ntoa(data[i+20:i+24])
            port = struct.unpack(">H", data[i+24:i+26])[0]
            self.add_node(nid, ip, port)

    # --- Mini Bencoder ---
    def bencode(self, data):
        if isinstance(data, int): return f"i{data}e".encode('utf-8')
        elif isinstance(data, bytes): return f"{len(data)}:".encode('utf-8') + data
        elif isinstance(data, str): return f"{len(data)}:".encode('utf-8') + data.encode('utf-8')
        elif isinstance(data, list):
            return b'l' + b''.join([self.bencode(x) for x in data]) + b'e'
        elif isinstance(data, dict):
            out = b'd'
            for k in sorted(data.keys()):
                out += self.bencode(k) + self.bencode(data[k])
            return out + b'e'