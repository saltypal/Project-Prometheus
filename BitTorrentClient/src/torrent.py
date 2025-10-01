from bencoding import bencodeDecode
from collections import deque
import pprint
import hashlib

"""

MADE BY SATYA PALADUGU AT 30/9/2025 7:55 PM
LAST MODIFIED: 0/9/2025 7:55 PM
"""

class Torrent:
    """
    This class deals with the torrent content, self.information that has to be retrieved from the torrent.
    1. Decoded Bencode
    2. self.InfoHash
    3. Torrent details
    4. Tracker List
    """
    
    def __init__(self, torrent_file_path):
        # Initialise the decoder to decode the bencode.
        self.decoder = bencodeDecode() 
        self.torrentFilePath = torrent_file_path
        # self.rawTorrent = None
        # self.cleanTorrent = None
        # self.info_hash = None
        self.total_size = 0
        self.announceList = None
        self.info = None
        self.load_torrentFile()
        self.decode_torrentFile()
        
    # ----------------------------------------
    """
        This block deals with the torrent file loading. 
        Variables: torrentFilePath: Has path of the torentfile
                   rawTorrent: has the queued contents of the torrentfile
                   cleanTorrent: has the decoded content
    """

    def load_torrentFile(self):
        """This function, loads the torrent file and returns the data in a queue"""
        try:
            with open(self.torrentFilePath,'rb') as rawTorrentFile:
                self.rawTorrent = rawTorrentFile.read()
                if self.rawTorrent:
                    print('Successfully loaded torrent file into bytes.')
                    return True
        except Exception as e:
            print(f"Sorry boss, I can't load the torrent file: {e}")
            return False
    
    def decode_torrentFile(self):
        """Decodes the raw torrent data. Assumes load_torrentFile has been called."""
        if not self.rawTorrent:
            print("Error: Torrent file not loaded. Call load_torrentFile() first.")
            return False
        
        # We pass a copy to the decoder so the original raw data is preserved
        rawTorrentDequeue = deque(self.rawTorrent)
        self.cleanTorrent = self.decoder.deBencode_list(rawTorrentDequeue)
        if self.cleanTorrent:
            print("Successfully decoded torrent file.")
            return True
        return False
    
    def write_decoded_to_file(self):
        """Writes the decoded torrent data to a text file for inspection."""
        if not self.cleanTorrent:
            print("Error: No decoded data to write.")
            return

        try:
            outputfile_name = self.torrentFilePath[:-8] + ".txt"
            with open(outputfile_name,'w', encoding='utf-8') as decodedtor:
                decodedtor.write(pprint.pformat(self.cleanTorrent))
                print(f"Successfully wrote decoded data to {outputfile_name}")
        except Exception as e:
            print(f"Couldnt write to file ma: {e}")


    #----------------------
    # Get self.info dictionary
    """
    self.INFO_HASH generation method:
                            for generating self.info_hash, i have to make a unique 20-byte SHA1 hash of the bencoded dictionary.
                            normally, you should bencode back to the ideal bencoded data, and then hash it. 
                            but this time, we will do something different BECAUSE IM F-ING LAZY.
                            for this, we will have to pinpoint where the b'self.info' is in the raw file and then take everything after it.
                            
    """
    def generate_hash(self, data):
        # SHA1 always makes 20Byte hashes
        # FIX: Added parentheses to call .digest()
        return hashlib.sha1(data).digest()

    def generate_info_hash(self):
        """
        This function is an attempt to create self.info hash without encoding the whole self.info_hash.
        """
        if not self.rawTorrent:
            print("Error: Raw torrent data not available.")
            return None

        word = b'4:info'
        rawData = self.rawTorrent
        
        print("OK Now lets generate info hash using the alt trick.")
        try:
            position = rawData.index(word) + len(word)
            print("ok i found 4:info. now let's proceed.")
        except ValueError:
            raise ValueError("Invalid Torrent File: Could not find b'4:info' key.")

        temp_data = rawData[position:]
        level = 0
        end_offset = 0
        i = 0
        
        if temp_data[i:i+1] == b'd':
            level = 1
            i = 1
        else:
            raise ValueError("Corrupt torrent: 'info' key not followed by a dictionary.")

        while i < len(temp_data):
            char = temp_data[i:i+1]

            if char == b'd' or char == b'l':
                level += 1
                i += 1
            elif char == b'e':
                level -= 1
                i += 1
            elif char in b'0123456789':
                colon_index = temp_data.find(b':', i)
                if colon_index == -1: 
                    raise ValueError("Corrupt torrent: string length not followed by a colon.")
                
                str_len = int(temp_data[i:colon_index])
                
                # Jump the index past the whole string: 'len' + ':' + data
                i = colon_index + 1 + str_len
            
            # --- THE REAL FUCKING FIX IS HERE ---
            elif char == b'i':
                # We need to find the closing 'e' and jump past it.
                end_of_int = temp_data.find(b'e', i)
                if end_of_int == -1:
                    raise ValueError("Corrupt torrent: integer not followed by 'e'.")
                i = end_of_int + 1
            # --- END OF THE FIX ---
            else:
                # Should not happen in a valid bencode file
                raise ValueError(f"Unexpected character in info dict: {char}")
            
            if level == 0:
                end_offset = i
                break

        if end_offset == 0:
            raise ValueError("Could not determine the end of the self.info dictionary.")
        
        # The slice should go from the start of the 'd' to the final 'e'
        raw_info_bytes = temp_data[:end_offset]
        print("Info dictionary raw bytes have been extracted.")
        
        self.info_hash = self.generate_hash(raw_info_bytes)
        if self.info_hash:
            print(f"Info_hash has been generated: {self.info_hash.hex()}")
        return self.info_hash
     

#-----------------------------------------------------
    """
    Everything related to calculation of total size
    """
    def calculate_total_size(self):
        """Calculates the total size of the torrent's content."""
        if not self.cleanTorrent:
            print("Error: Torrent is not decoded yet.")
            return 0
        
        self.info = self.cleanTorrent.get(b'info') # Getting the info directory of the torrent
        if not self.info:
            raise ValueError("Invalid torrent file: 'info' dictionary not found.")

        # FIX: Correctly calculates size for single and multi-file torrents.
        if b'length' in self.info:
            # Single file case
            self.total_size = self.info[b'length']
        elif b'files' in self.info:
            # Multi-file case
            self.total_size = sum(f[b'length'] for f in self.info[b'files'])
        else:
            self.total_size = 0
        
        print(f"Total torrent size: {self.total_size} bytes")
        return self.total_size

#-----------------------------------------------------
    """
    Pieces related.

    1. Getting pieces
    2.
    """
    def getPieces(self):
        """
        The pieces are in the info directory. 
        It is a string consisting of the concatenation of all 20-byte SHA1 hash values, one per piece (byte string, i.e. not urlencoded)
        
        """
        if not self.cleanTorrent:
            print("Error: Torrent is not decoded yet.")
            return 0
        if not self.info:
            raise ValueError("Invalid torrent file: 'info' dictionary not found.")
        self.pieces = self.info[b'pieces']
        if self.pieces:
            print("The torrent's pieces hashes are ready. ")
            print(self.pieces)
    
    def pieceHashGenerator():
        """
        This is to generate a 20Byte sha1 hash from the piece that was downloaded
        """
    
    
#-----------------------------------------------------
   

    
#-----------------------------------------------------
    """
    All getters and setters.s
    """
    def getRawTorrent(self):
        return self.rawTorrent
    
    def getCleanTorrent(self):
        return self.cleanTorrent

    def getInfoHash(self):
        return self.info_hash

    def getTotalSize(self):
        return self.total_size

    def getAnnounceList(self):
        self.announceList = self.cleanTorrent[b'announce']
        return self.announceList
        
#-------------------