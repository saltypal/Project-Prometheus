from client import client_Info
from tracker import Tracker
from torrent import Torrent
from session import Session
from peer2peer import PeerConnection
import pprint

"""
MADE BY SATYA PALADUGU
Refined for Architecture: The Controller Pattern (Step 6 Implementation)
"""

class bitTorrent_client:
    def __init__(self):
        # 1. Identity: Who are we?
        client = client_Info() 
        self.peerID = client.get_peerID() 
        self.portNumber = client.get_portNumber()
        print(f"Client Initialized with Peer ID: {self.peerID} on Port: {self.portNumber}")

    def start_torrent(self):   
        # NOTE: Ensure this path is correct for your machine
        file_path = r'BitTorrentClient\sample_torrent\cyberpunk2077.torrent'

        # ----------------------------------------------------
        # STEP 1: LOAD & PARSE (The Archivist)
        # ----------------------------------------------------
        print("\n--- Step 1: Loading Torrent ---")
        T = Torrent(file_path)
        
        info_hash = T.generate_info_hash()
        total_size = T.calculate_total_size()
        tracker_urls = T.getAnnounceList()
        
        if not tracker_urls:
            print("CRITICAL ERROR: No tracker URLs found.")
            return

        # ----------------------------------------------------
        # STEP 2: INITIALIZE SESSION (The Accountant)
        # ----------------------------------------------------
        print("\n--- Step 2: Initializing Session ---")
        S = Session(self.peerID, self.portNumber, total_size)

        # ----------------------------------------------------
        # STEP 3: CONTACT TRACKER (The Messenger)
        # ----------------------------------------------------
        print("\n--- Step 3: Contacting Trackers ---")
        Tr = Tracker(tracker_urls)
        
        peers_list, interval = Tr.get_peers(
            info_hash=info_hash,
            peer_id=self.peerID,
            port=self.portNumber,
            uploaded=S.getUploaded(),
            downloaded=S.getDownloaded(),
            left=S.getLeft()
        )

        # ----------------------------------------------------
        # STEP 4: PEER CONNECTION (The Handshake)
        # ----------------------------------------------------
        if peers_list:
            print(f"\n--- Step 4: Testing Handshake ---")
            print(f"Found {len(peers_list)} candidate peers.")
            
            # Let's try the first 5 peers (many might be offline/NAT'd)
            # We limit to 5 so we don't hang forever trying 50 dead IPs.
            for i in range(min(5, len(peers_list))):
                target_peer = peers_list[i]
                ip = target_peer[0]
                port = target_peer[1]
                
                print(f"\nAttempting to handshake with Peer {i+1}: {ip}:{port}")
                
                # Create the Connection Object (One object per peer)
                peer = PeerConnection(ip, port, info_hash, self.peerID)
                
                # 1. TCP Connect
                if peer.connect():
                    # 2. BitTorrent Handshake
                    if peer.perform_handshake():
                        print(">>> WE ARE OFFICIALLY IN THE SWARM! <<<")
                        print(">>> (We would start exchanging bitfields here) <<<")
                        peer.close()
                        break # Stop after one success for now to celebrate
                    else:
                        print("Handshake failed (Protocol mismatch or wrong info_hash).")
                        peer.close()
                else:
                    print("Connection failed (Peer offline or Firewall).")
        else:
            print("\n--- FAILURE: No peers found. Cannot proceed. ---")

if __name__ == '__main__':
    B = bitTorrent_client()
    B.start_torrent()