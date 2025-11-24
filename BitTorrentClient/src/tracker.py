import requests
from bencoding import bencodeDecode
from collections import deque
import struct

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

        
The Tracker response will be in bencode.
You are NOT decoding the announce URL list again.You are decoding the Answer the tracker sends back to you.

COUNTER STATEMENT:
You have hit a very common "real world" networking problem.

Remember, the Tracker is stateless.
It forgets you exist the moment the connection closes. Every time you talk to it,
you must re-introduce yourself and update your status from scratch

"""
class Tracker:
    def __init__(self, tracker_urls):
        """
        Initialize with a LIST of tracker URLs. The list will contain HTTP and UDP trackers. 
        We do NOT pass peerID or Session here. This class is just a specialized HTTP client.
        """
        self.tracker_urls = []
        
        # Ensure it's a list
        if isinstance(tracker_urls, list):
            self.tracker_urls = tracker_urls
        else:
            # If a single string was passed, wrap it in a list
            self.tracker_urls = [tracker_urls]
            
        # Ensure all are strings
        self.tracker_urls = [
            url.decode('utf-8') if isinstance(url, bytes) else url 
            for url in self.tracker_urls
        ]
            
        self.decoder = bencodeDecode()

    def get_peers(self, info_hash, peer_id, port, uploaded, downloaded, left):
        """
        The main public method. 
        Tries every URL in the list until one responds.
        """
        params = {
                'info_hash': info_hash, # The 20-byte SHA1 hash of the info dictionary
                'peer_id': peer_id, # The 20-byte ID you generated in client.py
                'port': port, # The port number you opened (e.g., 6882)
                'uploaded': uploaded, # Total bytes you have sent to other. rackers use this to calculate your "Share Ratio." Some private trackers ban you if you don't upload enough.
                'downloaded': downloaded, # Total bytes you have received.
                'left': left, # Bytes remaining (total_size - downloaded).
                
                'compact': 1, #What is it? A boolean flag (1 or 0).
                # Logic:
                # 0 (Verbose): The tracker sends a big list of dictionaries: [{'ip': '1.1.1.1', 'port': 80, 'peer_id': '...'}, ...]. This wastes bandwidth.
                # 1 (Compact): The tracker sends the 6-byte binary blobs we discussed (\x01\x01\x01\x01\x00\x50). It is much faster and smaller. Always use 1.

                'event': 'started' #string indicating your state change.
                #Options:
                # started: "I just came online. Add me to the swarm."
                # stopped: "I am closing the app. Delete me from the swarm."
                # completed: "I just finished the download! Move me from Leecher list to Seeder list."
                # (empty): "I am just sending a periodic 'I am still alive' heartbeat."
        }

        headers = {
            'User-Agent': 'SatyaTorrent/0.1'
        }
        # --- THE LOOP LOGIC ---
        for url in self.tracker_urls:
            try: 
                print(f"Contacting Tracker at: {url}")
                
                # Timeout set to 5s to fail faster if tracker is hanging
                # the format for requests is 
                # url, parameters (customized get request), headers
                response = requests.get(url, params=params, headers=headers, timeout=5)
                print(f"Response sent looks like : {response}")

                response.raise_for_status()
                # it checks the HTTP status code of the response:
                #  If the status code is 200–299 (success), nothing happens and your code continues.
                # If the status code is 400 or higher (client or server error), it raises an HTTPError exception.
                
                print("YESSSSSSSSSS LESGO Tracker responded.")
                
                # --- DEBUG PRINT: SHOW ME THE RAW DATA ---
                print(f"--- RAW RESPONSE FROM {url} ---")
                print(response.content)
                print("-----------------------------------")

                # If the first byte is '<', we know it's HTML garbage.
                if response.content.startswith(b'<'):
                    print(f"The tracker response starts with a <. \n Tis means Tracker {url} sent HTML instead of Bencode. Likely an error page.")
                    continue

                raw_response = deque(response.content)
                tracker_response = self.decoder.deBencode_list(raw_response)
                
                # Check for tracker error messages
                if b'failure reason' in tracker_response:
                    error_msg = tracker_response[b'failure reason'].decode('utf-8')
                    print(f"Tracker {url} refused: {error_msg}")
                    continue # Try the next tracker

                if b'peers' not in tracker_response:
                    print(f"Tracker {url} response has no 'peers' key.")
                    continue # Try the next tracker
                    
                # IF WE ARE HERE, SUCCESS!
                raw_peers = tracker_response[b'peers']
                interval = tracker_response.get(b'interval', 1800)
                
                print(f"Success with {url}! Interval: {interval}")
                peer_list = self._unpack_peers(raw_peers)
                return peer_list, interval

            except requests.exceptions.RequestException as e:
                print(f"Network Error contacting {url}: {e}")
                # Loop continues to next URL
                continue
            except Exception as e:
                print(f"Error parsing response from {url}: {e}")
                continue

        # If we loop through ALL and find nothing:
        print("All trackers failed.")
        return [], 0


    def _unpack_peers(self, raw_peers):
        """
        INTERNAL HELPER: Deciphers the 6-byte compact peer format.
        Format: [IP (4 bytes)] [Port (2 bytes)]
        """
        peers = []
        if len(raw_peers) % 6 != 0:
            print("Warning: Peer string length is not a multiple of 6.")
            
        for i in range(0, len(raw_peers), 6):
            chunk = raw_peers[i : i+6]
            if len(chunk) < 6:
                break
                
            ip = ".".join(str(b) for b in chunk[:4])
            port = struct.unpack('>H', chunk[4:])[0]
            peers.append((ip, port))
            
        print(f"Found {len(peers)} peers.")
        return peers

# class Tracker:
#         """
#         This class deals completely with contacting with tracker and maintaining a timed relationship between the tracker, getting and sending information

#         What are the things that the tracker class needs so that it communicates with the tracker:
#         1

#         """
#         # def __init__(self, peerID, portNum,info_hash,announceList,sizeOfTorrent,Session):

#         #         self.peerID = peerID
#         #         self.portNum = portNum
#         #         self.info_hash = info_hash
#         #         self.announceList = announceList
#         #         self.torrentSize = sizeOfTorrent
#         #         print("Tracker class is Ready. Proceeding...")
#         #         print(announceList)
#         #         self.getSession = Session
#         #         # self.additional = torrent()

#         # def keep_recieving_session(self):
#         #         self.downloaded = Session.getDownloaded()
#         #         self.uploaded = Session.getUploaded()


                
#         # """
#         # The thing about tracker is that, there are 2 types of protocols being used.
#         # one is the well known HTTPS connection that uses tcp. The other one is the udp connection that is more faster apparently. 
#         # udp is a part of BEP 15 implement
#         # """

#         # def make_tracker_Request(self, session: 'Session', event: str):
#         #          """
#         #     Builds and sends the announce request to the tracker.
#         #     'event' can be 'started', 'stopped', or 'completed'.
#         #     """
                
        
#         def __init__(self, announce_url):
#                 """
#                 Initialize with the address of the tracker (already extracted by Torrent).
#                 """
#                 # Always expect a string here; decode if bytes
#                 if isinstance(announce_url, bytes):
#                         self.announce_url = announce_url.decode('utf-8')
#                 else:
#                         self.announce_url = announce_url
#                 from bencoding import bencodeDecode
#                 self.decoder = bencodeDecode()

#         def get_peers(self, info_hash, peer_id, port, uploaded, downloaded, left):
#                 """
#                 The main public method. Call this to get the phonebook.
#                 Returns: (peer_list, interval)
#                 """
#                 import struct
#                 from collections import deque
#                 params = {
#                         'info_hash': info_hash,
#                         'peer_id': peer_id,
#                         'port': port,
#                         'uploaded': uploaded,
#                         'downloaded': downloaded,
#                         'left': left,
#                         'compact': 1,
#                         'event': 'started'
#                 }
#                 try:
#                         print(f"Contacting Tracker at: {self.announce_url}")
#                         response = requests.get(self.announce_url, params=params, timeout=10)
#                         response.raise_for_status()
#                         print("Tracker responded. Decoding...")
#                         raw_response = deque(response.content)
#                         tracker_response = self.decoder.deBencode_list(raw_response)
#                         if b'failure reason' in tracker_response:
#                                 error_msg = tracker_response[b'failure reason'].decode('utf-8')
#                                 raise ValueError(f"Tracker refused connection: {error_msg}")
#                         if b'peers' not in tracker_response:
#                                 raise ValueError("Tracker response did not contain a 'peers' list.")
#                         raw_peers = tracker_response[b'peers']
#                         interval = tracker_response.get(b'interval', 1800)
#                         print(f"Tracker request successful. Interval: {interval} seconds.")
#                         peer_list = self._unpack_peers(raw_peers)
#                         return peer_list, interval
#                 except requests.exceptions.RequestException as e:
#                         print(f"Network Error contacting tracker: {e}")
#                         return [], 0
#                 except Exception as e:
#                         print(f"Error parsing tracker response: {e}")
#                         return [], 0

#         def _unpack_peers(self, raw_peers):
#                 """
#                 INTERNAL HELPER: Deciphers the 6-byte compact peer format.
#                 Format: [IP (4 bytes)] [Port (2 bytes)]
#                 """
#                 import struct
#                 peers = []
#                 # Each peer is exactly 6 bytes.
#                 if len(raw_peers) % 6 != 0:
#                         print("Warning: Peer string length is not a multiple of 6.")
#                 # Loop through the string in chunks of 6
#                 for i in range(0, len(raw_peers), 6):
#                         chunk = raw_peers[i : i+6]
#                         if len(chunk) < 6:
#                                 break
#                         # 1. Extract IP (First 4 bytes)
#                         ip = ".".join(str(b) for b in chunk[:4])
#                         # 2. Extract Port (Last 2 bytes)
#                         port = struct.unpack('>H', chunk[4:])[0]
#                         peers.append((ip, port))
#                 print(f"Found {len(peers)} peers.")
#                 return peers


