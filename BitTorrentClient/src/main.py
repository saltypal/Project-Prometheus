from client import client_Info
from tracker import Tracker
from torrent import Torrent
from session import Session
from peer2peer import PeerConnection
from piece_manager import PieceManager
from server import Server 
import time
import threading
import random

"""
MADE BY SATYA PALADUGU
Main Entry Point.
Updated with TIT-FOR-TAT Choking Algorithm.
"""

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

        server = Server(self.portNumber, info_hash, self.peerID, pm)
        server.daemon = True 
        server.start()

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
            
            MAX_PEERS = 40 
            for i in range(min(MAX_PEERS, len(peers_list))):
                target_peer = peers_list[i]
                p = PeerConnection(
                    piece_manager=pm,
                    info_hash=info_hash,
                    peer_id=self.peerID,
                    ip=target_peer[0],
                    port=target_peer[1]
                )
                p.daemon = True
                p.start() 
                self.active_peers.append(p)
                
            print(f"Started {len(self.active_peers)} worker threads.")
            
            # START CHOKE MANAGER (Tit-for-Tat)
            choke_thread = threading.Thread(target=self.choke_manager_loop)
            choke_thread.daemon = True
            choke_thread.start()
            
            try:
                while True:
                    time.sleep(2)
            except KeyboardInterrupt:
                print("\nShutting down...")
        else:
            print("\n--- FAILURE: No peers found. ---")

    def choke_manager_loop(self):
        """
        The Tit-for-Tat Algorithm.
        Runs every 10 seconds.
        1. Measure speed of all peers.
        2. Unchoke Top 4 fastest.
        3. Optimistically Unchoke 1 random peer.
        4. Choke everyone else.
        """
        while True:
            time.sleep(10)
            
            # 1. Filter peers who are INTERESTED in us
            interested_peers = [p for p in self.active_peers if p.peer_interested and p.connected]
            if not interested_peers: continue

            # 2. Sort by Speed (Descending)
            # Note: This sorts based on how fast they uploaded TO US (Download Speed).
            # This is standard leech behavior. Seeders sort by Upload Speed.
            interested_peers.sort(key=lambda p: p.get_speed(), reverse=True)
            
            # 3. Pick Top 3 (Regular Unchoke)
            allowed_peers = interested_peers[:3]
            
            # 4. Optimistic Unchoke (Pick 1 random from the rest)
            remaining_peers = interested_peers[3:]
            if remaining_peers:
                optimistic_peer = random.choice(remaining_peers)
                allowed_peers.append(optimistic_peer)
            
            # 5. Apply Choke/Unchoke
            for p in interested_peers:
                if p in allowed_peers:
                    p.unchoke()
                else:
                    p.choke()
            
            # Debug Stats
            # print(f"--- Choke Round: Unchoked {len(allowed_peers)} peers ---")

if __name__ == '__main__':
    B = bitTorrent_client()
    B.start_torrent()