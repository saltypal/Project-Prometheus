import socket
import struct
import sys

"""
Refined by Satya's Architect
Handles the low-level TCP connection and Handshake with a single Peer.
"""

class PeerConnection:
    def __init__(self, ip, port, info_hash, peer_id):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash # Expecting 20 bytes (binary)
        self.peer_id = peer_id     # Expecting 20 bytes (binary)
        self.sock = None
        self.connected = False
        
        # We need a strict timeout. Peers come and go constantly.
        # If they don't answer in 5 seconds, we move on.
        self.timeout = 5

    def connect(self):
        """
        Establishes the raw TCP connection.
        """
        try:
            print(f"Connecting to {self.ip}:{self.port}...")
            # AF_INET = IPv4, SOCK_STREAM = TCP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.ip, self.port))
            print("TCP Connection Established!")
            return True
        except Exception as e:
            print(f"Failed to connect to {self.ip}:{self.port} - {e}")
            return False

    def perform_handshake(self):
        """
        Constructs and sends the handshake packet.
        Waits for a valid handshake response.
        """
        if not self.sock:
            print("Error: No socket connection.")
            return False

        # --- 1. BUILD THE MESSAGE ---
        # protocol identifier length: 19
        pstrlen = bytes([19]) 
        # protocol identifier string
        pstr = b'BitTorrent protocol'
        # 8 reserved bytes (all zeros)
        reserved = b'\x00' * 8
        
        # The Packet
        handshake_msg = pstrlen + pstr + reserved + self.info_hash + self.peer_id
        
        # --- 2. SEND THE MESSAGE ---
        try:
            self.sock.send(handshake_msg)
            print(f"Sent Handshake to {self.ip}")
        except Exception as e:
            print(f"Error sending handshake: {e}")
            return False

        # --- 3. RECEIVE THE RESPONSE ---
        try:
            # We expect exactly 68 bytes back for a standard handshake
            response = self.sock.recv(68)
            
            if len(response) < 68:
                print("Error: Peer disconnected or sent incomplete handshake.")
                return False
            
            # --- 4. PARSE & VERIFY ---
            # The structure is the same: [19][BitTorrent protocol][8 reserved][info_hash][peer_id]
            
            # Slice the response
            received_info_hash = response[28:48] # bytes 28 to 48 are the hash
            received_peer_id = response[48:68]   # bytes 48 to 68 are the ID

            if received_info_hash != self.info_hash:
                print(f"Error: Info Hash Mismatch! Peer has a different file.")
                # Logic: In reality, we might close connection here.
                return False
            
            print(f"Handshake Successful! Peer ID: {received_peer_id.hex()}")
            self.connected = True
            return True

        except Exception as e:
            print(f"Error receiving handshake: {e}")
            return False

    def close(self):
        if self.sock:
            self.sock.close()