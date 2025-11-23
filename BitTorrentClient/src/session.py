
from torrent import Torrent as T

class Session:
    """
    This class deals with managing the download, getting details about the work done and s
    ending it to the tracker class to update the main tracker.

    tracking the downloaded and pieces.
    """
    
    def __init__(self, peerID, portNum,sizeOfTorrent):
        self.peerID = peerID
        self.portNum = portNum
        self.sizeOfTorrent = sizeOfTorrent
        # self.GetPieceHash(self) = T.pieceHashGenerator()
        self.total_downloaded = 0
        self.total_uploaded = 0
    
    
    def getLeft(self):
        return self.sizeOfTorrent-self.total_downloaded
    
    def update_downloaded(self, download):
        self.total_downloaded += download

    def update_uploaded(self, upload):
        self.total_uploaded += upload

    """
    There has to be a function to keep track of the downloaded content.
    """