import hashlib
import os
import math
import time

"""
MADE BY SATYA PALADUGU
Utility to create STANDARD .torrent files (Bencoded).
Compatible with all BitTorrent clients.
"""

class TorrentCreator:
    def __init__(self, file_path, tracker_url="http://localhost:8000/announce", piece_size=262144):
        self.file_path = file_path
        self.tracker_url = tracker_url
        self.piece_size = piece_size # Default 256KB
        
    def create_torrent(self):
        if not os.path.exists(self.file_path):
            print(f"Error: File {self.file_path} not found.")
            return

        file_name = os.path.basename(self.file_path)
        file_size = os.path.getsize(self.file_path)
        
        print(f"Creating torrent for: {file_name} ({file_size} bytes)")
        
        # 1. Generate Pieces Hash
        pieces_hash = b''
        try:
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.piece_size)
                    if not chunk:
                        break
                    pieces_hash += hashlib.sha1(chunk).digest()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
                
        # 2. Create Dictionary Structure
        # Note: keys must be bytes or strings. Bencode handles utf-8 encoding.
        info_dict = {
            'name': file_name,
            'piece length': self.piece_size,
            'pieces': pieces_hash,
            'length': file_size
        }
        
        torrent_dict = {
            'announce': self.tracker_url,
            'created by': 'SatyaClient v1.0',
            'creation date': int(time.time()),
            'info': info_dict
        }
        
        # 3. Bencode and Save
        output_file = file_name + ".torrent"
        try:
            with open(output_file, 'wb') as f:
                f.write(self.bencode(torrent_dict))
            print(f"Success! Torrent saved to: {output_file}")
        except Exception as e:
            print(f"Failed to save torrent file: {e}")

    # --- Bencode Encoder ---
    def bencode(self, data):
        """
        Recursively encodes Python types into Bencode format.
        """
        if isinstance(data, int):
            # Integer: i<num>e
            return f"i{data}e".encode('utf-8')
            
        elif isinstance(data, (bytes, bytearray)):
            # Byte String: <len>:<data>
            return f"{len(data)}:".encode('utf-8') + data
            
        elif isinstance(data, str):
            # String: <len>:<utf-8 data>
            data_bytes = data.encode('utf-8')
            return f"{len(data_bytes)}:".encode('utf-8') + data_bytes
            
        elif isinstance(data, list):
            # List: l<item1><item2>e
            encoded = b'l'
            for item in data:
                encoded += self.bencode(item)
            return encoded + b'e'
            
        elif isinstance(data, dict):
            # Dictionary: d<key1><val1><key2><val2>e
            # Keys must be sorted as raw bytestrings
            encoded = b'd'
            # Sort keys ensures consistent hash
            sorted_keys = sorted(data.keys())
            
            for key in sorted_keys:
                # Keys must be bencoded (usually strings)
                encoded += self.bencode(key)
                encoded += self.bencode(data[key])
            return encoded + b'e'
            
        else:
            raise TypeError(f"Cannot bencode type: {type(data)}")

# Example Usage
if __name__ == "__main__":
    # Create a dummy file for testing if it doesn't exist
    test_filename = "test_data.txt"
    if not os.path.exists(test_filename):
        with open(test_filename, "w") as f:
            f.write("This is a test file for BitTorrent Phase 2." * 500)
            
    tc = TorrentCreator(test_filename) 
    tc.create_torrent()