from client import client_Info
from tracker import Tracker
from torrent import Torrent
from session import Session
import pprint
"""

MADE BY SATYA PALADUGU AT 30/9/2025 7:55 PM
LAST MODIFIED: 0/9/2025 7:55 PM
"""
class bitTorrent_client:
    def __init__(self):
     
    # First we have to initialise the client.
        client = client_Info() # Initialise a client object. Basically starting the client.
        self.peerID = client.get_peerID() # Generating a peerID for the session to represent the client
        self.portNumber = client.get_portNumber() # Getting the PortNumber
        # self.torrent_list = []

        print(f"Client Initialized with Peer ID: {self.peerID} on Port: {self.portNumber}")

# ----------------------------------------------------------------------------
    """
        To make the client compatible with multiple torrent downloads at the same time,
        we will create a function that will create a new object.
        Each object will represent one torrent download.
        For this, The BitTorrent Client object will be only one, But the objects will be multiple.

        We have to make the functions used by one torrent, individual to that torrent. 
        I.E, one function that will have a series of methods which are used by the torrent.
    """
        
    def start_torrent(self):   
        # NOTE: Ensure this path is correct for your machine
        file_path = r'BitTorrentClient\sample_torrent\cyberpunk2077.torrent'

        # ----------------------------------------------------
        # STEP 1: LOAD & PARSE (The Archivist)
        # ----------------------------------------------------
        print("\n--- Step 1: Loading Torrent ---")
        T = Torrent(file_path)
        
        # Get the critical data we need for the other components
        info_hash = T.generate_info_hash()
        total_size = T.calculate_total_size()
        tracker_urls = T.getAnnounceList() # This returns a LIST of strings now
        
        if not tracker_urls:
            print("CRITICAL ERROR: No tracker URLs found in torrent file.")
            return

        # ----------------------------------------------------
        # STEP 2: INITIALIZE SESSION (The Accountant)
        # ----------------------------------------------------
        print("\n--- Step 2: Initializing Session ---")
        # Session needs to know how much work we have (total_size)
        S = Session(self.peerID, self.portNumber, total_size)

        # ----------------------------------------------------
        # STEP 3: CONTACT TRACKER (The Messenger)
        # ----------------------------------------------------
        print("\n--- Step 3: Contacting Trackers ---")
        
        # We pass the LIST of URLs. Tracker is dumb; it just tries them one by one.
        Tr = Tracker(tracker_urls)
        
        # We manually pull dynamic stats from Session to give to Tracker
        peers_list, interval = Tr.get_peers(
            info_hash=info_hash,
            peer_id=self.peerID,
            port=self.portNumber,
            uploaded=S.getUploaded(),
            downloaded=S.getDownloaded(),
            left=S.getLeft()
        )

        # ----------------------------------------------------
        # STEP 4: PEER CONNECTION (The Workers) -> COMING SOON
        # ----------------------------------------------------
        if peers_list:
            print(f"\n--- SUCCESS: Found {len(peers_list)} peers ---")
            pprint.pprint(peers_list)
            
            # This is where we will eventually start Step 6 (Handshakes)
            # p2p = P2P(peers_list, info_hash, self.peerID)
            # p2p.start()
        else:
            print("\n--- FAILURE: No peers found. Cannot proceed. ---")

if __name__ == '__main__':
    B = bitTorrent_client()
    B.start_torrent()