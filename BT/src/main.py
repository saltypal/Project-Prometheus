from client import client_Info
from tracker import Tracker
from torrent import Torrent
"""

MADE BY SATYA PALADUGU AT 28/9/2025 11:40 AM
LAST MODIFIED: 29/9/2025 11:57AM 
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
        file = r'BT\sample_torrent\manjaro.torrent'

        # First load the torrent 
        T = Torrent(file)
        T.write_decoded_to_file()
        info_hash = T.generate_info_hash()
        size = T.calculate_total_size()

        # Tracker Creation
        Tr = Tracker(self.peerID,self.portNumber,T.getRawTorrent,T.getCleanTorrent,T.getInfoHash,T.getAnnounceList,T.getTotalSize)


if __name__ == '__main__':
    B = bitTorrent_client()
    B.start_torrent()