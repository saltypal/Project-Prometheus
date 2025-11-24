import socket
import struct
import threading
import time

"""
MADE BY SATYA PALADUGU
BEP 14: Local Peer Discovery (LPD) with Custom LAN Coordination.
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
        self.found_peers = set() 
        
        # Custom: Track if we are the Local Master
        self.is_master = False
        self.local_cluster_ids = {self.peer_id} # Set of all Peer IDs in LAN

    def run(self):
        self.running = True
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            recv_sock.bind(('', MCAST_PORT))
            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except:
            print("LPD: Bind Failed. LAN features disabled.")
            return

        recv_sock.settimeout(1)
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        except: pass

        print("--- LPD Service Started ---")
        last_announce = 0

        while self.running:
            if time.time() - last_announce > 60:
                self.announce(send_sock)
                last_announce = time.time()

            try:
                data, addr = recv_sock.recvfrom(1024)
                self.handle_message(data, addr)
            except socket.timeout:
                continue
            except Exception:
                pass

    def announce(self, sock):
        # We include our Peer ID in the message for election purposes
        msg = (
            f"BT-SEARCH * HTTP/1.1\r\n"
            f"Host: {MCAST_GRP}:{MCAST_PORT}\r\n"
            f"Port: {self.port}\r\n"
            f"Infohash: {self.info_hash.hex()}\r\n"
            f"PeerID: {self.peer_id.hex()}\r\n" 
            f"\r\n\r\n"
        ).encode('utf-8')
        try: sock.sendto(msg, (MCAST_GRP, MCAST_PORT))
        except: pass

    def handle_message(self, data, addr):
        try:
            msg = data.decode('utf-8', errors='ignore')
            if "BT-SEARCH" in msg and f"Infohash: {self.info_hash.hex()}" in msg:
                remote_id = None
                remote_port = 0
                
                for line in msg.split('\r\n'):
                    if line.startswith("Port:"):
                        remote_port = int(line.split(":")[1].strip())
                    if line.startswith("PeerID:"):
                        remote_id = bytes.fromhex(line.split(":")[1].strip())

                if remote_id and remote_port > 0:
                    if remote_id == self.peer_id: return

                    # Election Logic: Lowest ID becomes Master
                    self.local_cluster_ids.add(remote_id)
                    min_id = min(self.local_cluster_ids)
                    self.is_master = (min_id == self.peer_id)
                    
                    peer = (addr[0], remote_port)
                    if peer not in self.found_peers:
                        print(f"LPD: Found Local Peer {peer} (Master={self.is_master})")
                        self.found_peers.add(peer)
        except: pass

    def get_new_peers(self):
        peers = list(self.found_peers)
        self.found_peers.clear()
        return peers