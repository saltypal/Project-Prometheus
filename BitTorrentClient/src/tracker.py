import hashlib
import requests
import torrent
import client
"""

MADE BY SATYA PALADUGU AT 28/9/2025 11:40 PM
LAST MODIFIED: 29/9/2025 11:57AM 

        
This file deals with:
1. info_hash
2. Request generation for HTTP and UDP trackers.
3. Response acceptance


key parameters your client must include in the request:
info_hash: This is a 20-byte SHA1 hash of the bencoded info dictionary from the torrent file. This hash uniquely identifies the torrent on the netw
uploaded: The total amount of data you've uploaded in bytes. Starts at 0.
downloaded: The total amount of data you've downloaded in bytes. Starts at 0.
left: The number of bytes remaining to be downloaded.
event: This parameter tells the tracker what's happening. The most common events are:
        started: Sent when your client first begins downloading.
        completed: Sent when you finish downloading the file.
        stopped: Sent when you close the client.
        (No event): Sent for periodic updates while downloading.


"""

class Tracker:
        """
        This is the tracker class. This class consists of functions that handle with 
        1. hash generation.
        """
        def __init__(self, peerID, portNum,rawTorrent,cleanTorrent,info_hash,announceList,sizeOfTorrent,):

                self.peerID = peerID
                self.portNum = portNum
                self.info_hash = info_hash
                self.rawTorrent = rawTorrent
                self.cleanTorrent = cleanTorrent
                self.announceList = announceList
                self.torrentSize = sizeOfTorrent
                print("Tracker is Ready. Proceeding...")

       