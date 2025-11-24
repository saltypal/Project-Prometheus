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

"""
MADE BY SATYA PALADUGU
Main Entry Point.
Updated with DHT, LPD, and Tit-for-Tat Choking.
"""

# CONFIGURATION
ENABLE_DHT = True # Set to True to join the Distributed Hash Table

class bitTorrent_client:
    def __init__(self):
        client = client_Info() 
        self.peerID = client.get_peerID() 
        self.portNumber = client.get_portNumber()
        self.active_peers = [] # List of PeerConnection threads
        print(f"Client Initialized. ID: {self.peerID}")

    def start_torrent(self):   
        file_path = r'BitTorrentClient\sample_torrent\debian-12.8.0-amd64-netinst.iso.torrent'

        print("--- Loading Torrent ---")
        try:
            T = Torrent(file_path)
            if not T.cleanTorrent: return
        except Exception as e:
            print(f"Failed to load torrent: {e}")
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

        print("--- Initializing Brain ---")
        pm = PieceManager(T) 

        # 1. Start Server (Incoming TCP)
        server = Server(self.portNumber, info_hash, self.peerID, pm)
        server.daemon = True 
        server.start()

        # 2. Start DHT Node (UDP) - BEP 5
        if ENABLE_DHT:
            dht = DHTNode(self.portNumber, self.peerID)
            dht.daemon = True
            dht.start()
            print("DHT Node: Enabled")
        else:
            print("DHT Node: Disabled")

        # 3. Start Local Peer Discovery (Multicast UDP) - BEP 14
        lpd = LPD(info_hash, self.peerID, self.portNumber)
        lpd.daemon = True
        lpd.start()

        # 4. Contact Trackers (Main Discovery)
        print(f"--- Contacting Trackers ({len(combined_trackers)}) ---")
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
            print(f"\n--- Unleashing the Swarm ({len(peers_list)} peers) ---")
            
            # Track connected peers to avoid duplicates
            connected_peers = set()
            MAX_PEERS = 40 
            
            # Helper function to add a peer
            def add_peer(ip, port):
                if (ip, port) in connected_peers: return
                if len(self.active_peers) >= MAX_PEERS: return
                
                connected_peers.add((ip, port))
                p = PeerConnection(pm, info_hash, self.peerID, ip=ip, port=port)
                p.daemon = True
                p.start()
                self.active_peers.append(p)

            # Initial Peers from Tracker
            for ip, port in peers_list:
                add_peer(ip, port)
                
            print(f"Started {len(self.active_peers)} worker threads.")
            
            # 5. Start Choke Manager (Tit-for-Tat)
            choke_thread = threading.Thread(target=self.choke_manager_loop)
            choke_thread.daemon = True
            choke_thread.start()
            
            # 6. Main Loop (Periodic Updates)
            try:
                while True:
                    time.sleep(5)
                    
                    # Check LPD for new local peers
                    local_peers = lpd.get_new_peers()
                    if local_peers:
                        print(f"LPD: Adding {len(local_peers)} local peers to swarm.")
                        for ip, port in local_peers:
                            add_peer(ip, port)
                            
            except KeyboardInterrupt:
                print("\nShutting down...")
                
        else:
            print("\n--- FAILURE: No peers found via Trackers. ---")
            print("Waiting for LPD...")
            try:
                while True: time.sleep(1)
            except: pass

    def choke_manager_loop(self):
        """
        The Tit-for-Tat Algorithm.
        Runs every 10 seconds.
        """
        while True:
            time.sleep(10)
            
            interested_peers = [p for p in self.active_peers if p.peer_interested and p.connected]
            if not interested_peers: continue

            # Sort by Download Speed (Fastest first)
            interested_peers.sort(key=lambda p: p.get_speed(), reverse=True)
            
            # Top 3 = Unchoke
            allowed_peers = interested_peers[:3]
            
            # Optimistic Unchoke (1 random)
            remaining_peers = interested_peers[3:]
            if remaining_peers:
                optimistic_peer = random.choice(remaining_peers)
                allowed_peers.append(optimistic_peer)
            
            # Apply Logic
            for p in interested_peers:
                if p in allowed_peers:
                    p.unchoke()
                else:
                    p.choke()

if __name__ == '__main__':
    B = bitTorrent_client()
    B.start_torrent()