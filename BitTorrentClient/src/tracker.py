import hashlib
import requests
import torrent
import client
from session import Session 
"""

MADE BY SATYA PALADUGU AT 30/9/2025 7:55 PM
LAST MODIFIED: 0/9/2025 7:55 PM

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
        This class deals completely with contacting with tracker and maintaining a timed relationship between the tracker, getting and sending information

        What are the things that the tracker class needs so that it communicates with the tracker:
        1

        """
        def __init__(self, peerID, portNum,info_hash,announceList,sizeOfTorrent):

                self.peerID = peerID
                self.portNum = portNum
                self.info_hash = info_hash
                self.announceList = announceList
                self.torrentSize = sizeOfTorrent
                print("Tracker is Ready. Proceeding...")
                print(announceList)
                # self.additional = torrent()


                
        """
        The thing about tracker is that, there are 2 types of protocols being used.
        one is the well known HTTPS connection that uses tcp. The other one is the udp connection that is more faster apparently. 
        udp is a part of BEP 15 implement
        """

        def make_tracker_Request(self, session: 'Session', event: str):
                 """
            Builds and sends the announce request to the tracker.
            'event' can be 'started', 'stopped', or 'completed'.
            """
                