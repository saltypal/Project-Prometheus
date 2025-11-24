from client import client_Info
from tracker import Tracker
from torrent import Torrent
from session import Session
from peer2peer import PeerConnection
from piece_manager import PieceManager
from server import Server
from dht import DHTNode  
from lpd import LPD      
import time
import threading
import random
from tqdm import tqdm

"""
MADE BY SATYA PALADUGU
Main Entry Point.
Updated with Custom LAN Partitioning Strategy.
"""

ENABLE_DHT = True 

class bitTorrent_client:
    def __init__(self):
        print("\n" + "="*50)
        print("      SATYA BITTORRENT CLIENT v1.0      ")
        print("="*50 + "\n")
        
        client = client_Info() 
        self.peerID = client.get_peerID() 
        self.portNumber = client.get_portNumber()
        self.active_peers = [] 
        
        print(f"[INFO] Client ID: {self.peerID.hex()}")

    def start_torrent(self):   
        file_path = r'BitTorrentClient\sample_torrent\debian-12.8.0-amd64-netinst.iso.torrent'

        print(f"\n=== STEP 1: LOADING METADATA ===")
        try:
            T = Torrent(file_path)
            if not T.cleanTorrent: return
        except Exception as e:
            print(f"[ERROR] Failed to load torrent: {e}")
            return

        info_hash = T.generate_info_hash()
        total_size = T.calculate_total_size()
        tracker_urls = T.getAnnounceList()
        
        public_trackers = [
            'udp://tracker.opentrackr.org:1337/announce',
            'udp://9.rarbg.com:2810/announce',
            'udp://tracker.openbittorrent.com:80/announce',
            'http://tracker.openbittorrent.com:80/announce',
            'udp://opentracker.i2p.rocks:6969/announce'
        ]
        combined_trackers = list(set(tracker_urls + public_trackers))

        print(f"\n=== STEP 2: INITIALIZING STORAGE ===")
        pm = PieceManager(T) 

        print(f"\n=== STEP 3: STARTING SERVICES ===")
        server = Server(self.portNumber, info_hash, self.peerID, pm)
        server.daemon = True 
        server.start()
        print("   [+] TCP Server Started")

        if ENABLE_DHT:
            dht = DHTNode(self.portNumber, self.peerID)
            dht.daemon = True
            dht.start()
            print("   [+] DHT Node Started")

        lpd = LPD(info_hash, self.peerID, self.portNumber)
        lpd.daemon = True
        lpd.start()
        print("   [+] LPD Service Started (Custom LAN Partitioning)")

        print(f"\n=== STEP 4: DISCOVERY ===")
        Tr = Tracker(combined_trackers)
        S = Session(self.peerID, self.portNumber, total_size)
        
        peers_list, interval = Tr.get_peers(
            info_hash=info_hash,
            peer_id=self.peerID,
            port=self.portNumber,
            uploaded=S.getUploaded(),
            downloaded=S.getDownloaded(),
            left=S.getLeft()
        )

        if peers_list:
            print(f"\n=== STEP 5: UNLEASHING SWARM ===")
            connected_peers = set()
            MAX_PEERS = 40 
            
            def add_peer(ip, port, is_local=False):
                if (ip, port) in connected_peers: return
                if len(self.active_peers) >= MAX_PEERS: return
                
                connected_peers.add((ip, port))
                p = PeerConnection(pm, info_hash, self.peerID, ip=ip, port=port)
                # If local, we tag it so PieceManager knows
                if is_local:
                    # In a real implementation, we'd set a flag on the PeerConnection
                    # which then propagates to PieceManager.update_peer
                    pass 
                p.daemon = True
                p.start()
                self.active_peers.append(p)

            for ip, port in peers_list:
                add_peer(ip, port)
                
            # Start Choke Manager
            choke_thread = threading.Thread(target=self.choke_manager_loop)
            choke_thread.daemon = True
            choke_thread.start()
            
            print("\n=== DOWNLOAD IN PROGRESS ===")
            try:
                while True:
                    time.sleep(5)
                    # LPD Check
                    local_peers = lpd.get_new_peers()
                    if local_peers:
                        tqdm.write(f"[LPD] Found {len(local_peers)} local peers. Activating Partition Strategy.")
                        for ip, port in local_peers:
                            add_peer(ip, port, is_local=True)
                            
            except KeyboardInterrupt:
                print("\n[!] Shutting down...")
        else:
            print("\n[!] FAILURE: No peers found.")
            try:
                while True: time.sleep(1)
            except: pass

    def choke_manager_loop(self):
        while True:
            time.sleep(10)
            interested_peers = [p for p in self.active_peers if p.peer_interested and p.connected]
            if not interested_peers: continue
            interested_peers.sort(key=lambda p: p.get_speed(), reverse=True)
            allowed_peers = interested_peers[:3]
            remaining_peers = interested_peers[3:]
            if remaining_peers:
                optimistic_peer = random.choice(remaining_peers)
                allowed_peers.append(optimistic_peer)
            for p in interested_peers:
                if p in allowed_peers: p.unchoke()
                else: p.choke()

if __name__ == '__main__':
    B = bitTorrent_client()
    B.start_torrent()