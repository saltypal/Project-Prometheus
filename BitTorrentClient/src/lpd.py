import socket
import struct
import threading
import time

"""
MADE BY SATYA PALADUGU
BEP 14: Local Peer Discovery.
Multicasts presence on LAN to find local peers.
"""

MCAST_GRP = '239.192.152.143'
MCAST_PORT = 6771

class LPD(threading.Thread):
    def __init__(self, info_hash, peer_id, port):
        threading.Thread.__init__(self)
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.port = port
        self.running = False
        self.found_peers = set() # (ip, port)

    def run(self):
        self.running = True
        
        # 1. Setup Listener Socket (Receive)
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except: pass
        
        try:
            # Bind to all interfaces on port 6771
            recv_sock.bind(('', MCAST_PORT))
        except:
            print("LPD: Could not bind port 6771. LPD disabled.")
            return

        # Join Multicast Group
        try:
            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except:
            pass 

        recv_sock.settimeout(1)

        # 2. Setup Sender Socket (Broadcast)
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        except: pass

        print("--- LPD Service Started ---")

        last_announce = 0

        while self.running:
            # A. Announce every 60 seconds
            if time.time() - last_announce > 60:
                self.announce(send_sock)
                last_announce = time.time()

            # B. Listen for others
            try:
                data, addr = recv_sock.recvfrom(1024)
                self.handle_message(data, addr)
            except socket.timeout:
                continue
            except Exception:
                pass

    def announce(self, sock):
        """
        Sends the BT-SEARCH message.
        """
        msg = (
            f"BT-SEARCH * HTTP/1.1\r\n"
            f"Host: {MCAST_GRP}:{MCAST_PORT}\r\n"
            f"Port: {self.port}\r\n"
            f"Infohash: {self.info_hash.hex()}\r\n"
            f"\r\n\r\n"
        ).encode('utf-8')
        
        try:
            sock.sendto(msg, (MCAST_GRP, MCAST_PORT))
        except:
            pass

    def handle_message(self, data, addr):
        try:
            msg = data.decode('utf-8', errors='ignore')
            
            if "BT-SEARCH" in msg and f"Infohash: {self.info_hash.hex()}" in msg:
                for line in msg.split('\r\n'):
                    if line.startswith("Port:"):
                        port = int(line.split(":")[1].strip())
                        
                        # Don't add ourselves
                        if port == self.port: continue 
                        
                        peer = (addr[0], port)
                        if peer not in self.found_peers:
                            print(f"LPD: Found Local Peer at {peer}")
                            self.found_peers.add(peer)
        except:
            pass

    def get_new_peers(self):
        """Called by main loop to fetch found LAN peers"""
        peers = list(self.found_peers)
        self.found_peers.clear() # Clear so we don't re-add them
        return peers