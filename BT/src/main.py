from client import client_Info
from bencoding import bencodeDecode
from collections import deque
import pprint
class bitTorrent_client:
    def __init__(self):
     
    # First we have to initialise the client.
        client = client_Info()
        self.peerID = client.generateID()
        self.portNumber = client.getPortNumber()
        self.initialise_decoder()
        print(f"Client Initialized with Peer ID: {self.peerID} on Port: {self.portNumber}")

     

# ----------------------------------------------------------------------------
    """
        This block deals with the torrent file loading. 
        Variables: torrentFilePath: Has path of the torentfile
                    rawTorrent: has the queued contents of the torrentfile
                    decodedTorrent: has the decoded content
    """
    def return_torrentPath(self):
        """For this function, it is used to select the torrent path in the ui or whatever and return the path of the torrent file"""
        self.torrentFilePath = r'BT\sample_torrent\bopbop.torrent'


    def load_torrentFile(self):
        """This function, loads the torrent file and returns the data in a queue"""
        try:
            with open(self.torrentFilePath,'rb') as rawTorrent:
                non_queue_data = rawTorrent.read()
                self.rawTorrent = deque(non_queue_data)

        except Exception as e:
            print(f"Sorry boss, I can't load the torrent file: {e}")
    
    def initialise_decoder(self):
        self.decoder = bencodeDecode()

    def decode_torrentFile(self):
        self.decodedTorrent = self.decoder.deBencode_list(self.rawTorrent)
    
    def write_decoded_to_file(self):
        try:
            outputfile_name = self.torrentFilePath[:-8]+".txt"
            with open(outputfile_name,'w') as decodedtor:
                decodedtor.write(pprint.pformat(self.decodedTorrent))
                print(f"Successfully wrote decoded data to {outputfile_name}")
        except Exception as e:
            print(f"Couldnt write to file ma: {e}")

# ----------------------------------------------------------------------------

if __name__ == '__main__':  
    # client object creating
    f = bitTorrent_client()

    # loading one torrent
    f.return_torrentPath()
    f.load_torrentFile()
    f.decode_torrentFile()

    # writing the torrent decoded content into a file.
    # f.write_decoded_to_file() t