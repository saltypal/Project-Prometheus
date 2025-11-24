import requests
from bencoding import bencodeDecode
from collections import deque
import struct
from urllib.parse import quote

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
You are NOT decoding the announce URL list again. You are decoding the Answer the tracker sends back to you.

COUNTER STATEMENT:
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
        # URL encode the binary parameters properly
        params = {
            'info_hash': info_hash,
            'peer_id': peer_id,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'compact': 1,
            'event': 'started'
        }

        headers = {
            'User-Agent': 'SatyaTorrent/0.1'
        }
        
        # --- THE LOOP LOGIC ---
        for url in self.tracker_urls:
            try: 
                print(f"Contacting Tracker at: {url}")
                
                # Timeout set to 5s to fail faster if tracker is hanging
                response = requests.get(url, params=params, headers=headers, timeout=5)
                print(f"Response status: {response.status_code}")

                response.raise_for_status()
                
                print("✓ Tracker responded successfully.")
                
                # --- DEBUG PRINT: SHOW ME THE RAW DATA ---
                print(f"--- RAW RESPONSE FROM {url} ---")
                print(response.content[:100])  # Print first 100 bytes
                print("-----------------------------------")

                # If the first byte is '<', we know it's HTML garbage.
                if response.content.startswith(b'<'):
                    print(f"ERROR: Tracker {url} sent HTML instead of Bencode. Likely an error page.")
                    continue

                # Decode the bencoded response
                raw_response = deque(response.content)
                tracker_response = self.decoder.deBencode_list(raw_response)
                
                # Check for tracker error messages
                if b'failure reason' in tracker_response:
                    error_msg = tracker_response[b'failure reason'].decode('utf-8')
                    print(f"✗ Tracker {url} refused: {error_msg}")
                    continue

                if b'peers' not in tracker_response:
                    print(f"✗ Tracker {url} response has no 'peers' key.")
                    print(f"Available keys: {list(tracker_response.keys())}")
                    continue
                    
                # IF WE ARE HERE, SUCCESS!
                raw_peers = tracker_response[b'peers']
                interval = tracker_response.get(b'interval', 1800)
                
                print(f"✓ Success with {url}! Interval: {interval}s")
                peer_list = self._unpack_peers(raw_peers)
                return peer_list, interval

            except requests.exceptions.RequestException as e:
                print(f"✗ Network Error contacting {url}: {e}")
                continue
            except Exception as e:
                print(f"✗ Error parsing response from {url}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # If we loop through ALL and find nothing:
        print("✗ All trackers failed.")
        return [], 0


    def _unpack_peers(self, raw_peers):
        """
        INTERNAL HELPER: Deciphers the 6-byte compact peer format.
        Format: [IP (4 bytes)] [Port (2 bytes)]
        """
        peers = []
        if len(raw_peers) % 6 != 0:
            print(f"Warning: Peer string length ({len(raw_peers)}) is not a multiple of 6.")
            
        for i in range(0, len(raw_peers), 6):
            chunk = raw_peers[i : i+6]
            if len(chunk) < 6:
                break
                
            ip = ".".join(str(b) for b in chunk[:4])
            port = struct.unpack('>H', chunk[4:])[0]
            peers.append((ip, port))
            
        print(f"✓ Found {len(peers)} peers.")
        return peers