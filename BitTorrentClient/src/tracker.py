import random
import socket
import requests
from bencoding import bencodeDecode
from collections import deque
import struct
from urllib.parse import quote, urlparse

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
        self.tracker_urls = []
        if isinstance(tracker_urls, list):
            self.tracker_urls = tracker_urls
        else:
            self.tracker_urls = [tracker_urls]
            
        self.tracker_urls = [
            url.decode('utf-8') if isinstance(url, bytes) else url 
            for url in self.tracker_urls
        ]
            
        self.decoder = bencodeDecode()

    def get_peers(self, info_hash, peer_id, port, uploaded, downloaded, left):
        all_peers = set() 
        final_interval = 1800

        for url in self.tracker_urls:
            try:
                peers = []
                interval = 1800

                if url.startswith('http'):
                    peers, interval = self.http_scrape(url, info_hash, peer_id, port, uploaded, downloaded, left)
                elif url.startswith('udp'):
                    peers, interval = self.udp_scrape(url, info_hash, peer_id, port, uploaded, downloaded, left)
                
                if peers:
                    print(f"   ✓ [SUCCESS] {url} -> {len(peers)} peers")
                    for p in peers:
                        all_peers.add(p)
                    final_interval = interval
                else:
                    pass 
                    # print(f"   x [FAIL] {url}")

            except Exception as e:
                pass

        unique_peers_list = list(all_peers)
        return unique_peers_list, final_interval
    
    # If the tracker is an Http tracker
    def http_scrape(self, url, info_hash, peer_id, port, uploaded, downloaded, left):
        params = {
            'info_hash': info_hash,
            'peer_id': peer_id,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'compact': 1,
            'event': 'started',
            'numwant': 100 
        }
        headers = {'User-Agent': 'SatyaTorrent/0.1'}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=2) 
            response.raise_for_status()
            
            if response.content.startswith(b'<'): return [], 0

            raw_response = deque(response.content)
            tracker_response = self.decoder.deBencode_list(raw_response)
            
            if b'failure reason' in tracker_response: return [], 0
                
            raw_peers = tracker_response[b'peers']
            interval = tracker_response.get(b'interval', 1800)
            return self._unpack_peers(raw_peers), interval

        except Exception:
            return [], 0

    
    def udp_scrape(self, url, info_hash, peer_id, port, uploaded, downloaded, left):
        parsed = urlparse(url)
        hostname = parsed.hostname
        port_num = parsed.port
        if not port_num: port_num = 80
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2) 

        try:
            connection_id = self._udp_send_connect(sock, hostname, port_num)
            peers, interval = self._udp_send_announce(
                sock, hostname, port_num, connection_id, 
                info_hash, peer_id, port, uploaded, downloaded, left
            )
            return peers, interval

        except Exception:
            return [], 0
        finally:
            sock.close()

    def _udp_send_connect(self, sock, hostname, port):
        protocol_id = 0x41727101980
        action = 0
        transaction_id = random.randint(0, 65535)
        packet = struct.pack("!QII", protocol_id, action, transaction_id)
        sock.sendto(packet, (hostname, port))
        data, addr = sock.recvfrom(2048)
        
        if len(data) < 16: raise ValueError("Short response")
        res_action, res_trans_id, connection_id = struct.unpack("!IIQ", data[:16])
        if res_trans_id != transaction_id: raise ValueError("ID mismatch")
        return connection_id

    def _udp_send_announce(self, sock, hostname, port, connection_id, info_hash, peer_id, my_port, uploaded, downloaded, left):
        action = 1
        transaction_id = random.randint(0, 65535)
        key = random.randint(0, 65535)
        
        packet = struct.pack("!QII20s20sQQQIIIiH",
            connection_id, action, transaction_id, info_hash, peer_id,
            downloaded, left, uploaded, 0, 0, key, 100, my_port
        )
        sock.sendto(packet, (hostname, port))
        data, addr = sock.recvfrom(4096)
        
        if len(data) < 20: raise ValueError("Short response")
        res_action, res_trans_id, interval, leechers, seeders = struct.unpack("!IIIII", data[:20])
        if res_trans_id != transaction_id: raise ValueError("ID mismatch")
        
        return self._unpack_peers(data[20:]), interval

    def _unpack_peers(self, raw_peers):
        peers = []
        for i in range(0, len(raw_peers), 6):
            chunk = raw_peers[i : i+6]
            if len(chunk) < 6: break
            ip = ".".join(str(b) for b in chunk[:4])
            port = struct.unpack('>H', chunk[4:])[0]
            peers.append((ip, port))
        return peers