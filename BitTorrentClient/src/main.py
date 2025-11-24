from client import client_Info
from tracker import Tracker
from torrent import Torrent
from session import Session
from peer2peer import PeerConnection
from piece_manager import PieceManager
from server import Server 
import time
import threading

"""
MADE BY SATYA PALADUGU
Main Entry Point.
Updated for MULTIPLE TORRENTS support.
"""

class TorrentSession(threading.Thread):
    """
    Manages a SINGLE torrent download/upload lifecycle.
    Runs as a thread so Main can handle multiple sessions.
    """
    def __init__(self, torrent_path, client_id, port):
        threading.Thread.__init__(self)
        self.torrent_path = torrent_path
        self.client_id = client_id
        self.port = port
        self.running = False
        self.workers = []
        
    def run(self):
        self.running = True
        print(f"--- Starting Session: {self.torrent_path} ---")
        
        try:
            T = Torrent(self.torrent_path)
            if not T.cleanTorrent: return
        except Exception as e:
            print(f"Failed to load torrent: {e}")
            return

        info_hash = T.generate_info_hash()
        total_size = T.calculate_total_size()
        tracker_urls = T.getAnnounceList()
        
        # Booster Trackers
        public_trackers = [
            'udp://tracker.opentrackr.org:1337/announce',
            'udp://9.rarbg.com:2810/announce',
            'udp://tracker.openbittorrent.com:80/announce',
            'http://tracker.openbittorrent.com:80/announce'
        ]
        combined_trackers = list(set(tracker_urls + public_trackers))

        pm = PieceManager(T) 

        # 1. Start Server for this torrent (Listening on same port? Need logic for sharing port)
        # For simplicity in this Phase, we assume 1 Server handles all, 
        # BUT PeerConnection logic needs mapping. 
        # TRICK: We pass the Server reference to Main, or assume 1 port = 1 torrent for now.
        # Let's stick to "Client Mode" for multiple torrents to avoid Port Conflicts in this simple version.
        
        # 2. Get Peers
        Tr = Tracker(combined_trackers)
        S = Session(self.client_id, self.port, total_size)
        
        peers_list, interval = Tr.get_peers(
            info_hash=info_hash,
            peer_id=self.client_id,
            port=self.port,
            uploaded=S.getUploaded(),
            downloaded=S.getDownloaded(),
            left=S.getLeft()
        )

        if peers_list:
            # 3. Start Workers
            MAX_PEERS = 20 
            for i in range(min(MAX_PEERS, len(peers_list))):
                if not self.running: break
                target_peer = peers_list[i]
                p = PeerConnection(
                    piece_manager=pm,
                    info_hash=info_hash,
                    peer_id=self.client_id,
                    ip=target_peer[0],
                    port=target_peer[1]
                )
                p.daemon = True
                p.start() 
                self.workers.append(p)
                
            # Keep alive loop for this session
            while self.running:
                time.sleep(5)
                # Check if complete?
        else:
            print(f"--- {self.torrent_path}: No peers found. ---")

    def stop(self):
        self.running = False
        # Workers are daemons, will die with main process

class bitTorrent_client:
    def __init__(self):
        client = client_Info() 
        self.peerID = client.get_peerID() 
        self.portNumber = client.get_portNumber()
        self.sessions = []
        print(f"Client Initialized. ID: {self.peerID}")

    def add_torrent(self, file_path):
        """Adds and starts a new torrent session"""
        session = TorrentSession(file_path, self.peerID, self.portNumber)
        session.daemon = True
        session.start()
        self.sessions.append(session)

    def main_loop(self):
        try:
            while True:
                command = input(">> (add [path] / list / quit): ").strip().split()
                if not command: continue
                
                if command[0] == "add":
                    if len(command) > 1:
                        self.add_torrent(command[1])
                    else:
                        print("Usage: add <path_to_torrent>")
                elif command[0] == "list":
                    print(f"Active Sessions: {len(self.sessions)}")
                elif command[0] == "quit":
                    break
        except KeyboardInterrupt:
            print("\nShutting down...")

if __name__ == '__main__':
    B = bitTorrent_client()
    # Auto-load the default for testing
    default_file = r'BitTorrentClient\sample_torrent\deb.torrent'
    B.add_torrent(default_file)
    
    B.main_loop()