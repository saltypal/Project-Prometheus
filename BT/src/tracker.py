import hashlib

"""

MADE BY SATYA PALADUGU AT 28/9/2025 11:40 PM
LAST MODIFIED: 29/9/2025 11:57AM 

        
This file deals with:
1. info_hash
2. Request generation for HTTP and UDP trackers.
3. Response acceptance


INFO_HASH generation method:
                            for generating info_hash, i have to make a unique 20-byte SHA1 hash of the bencoded dictionary.
                            normally, you should bencode back to the ideal bencoded data, and then hash it. 
                            but this time, we will do something different BECAUSE IM F-ING LAZY.
                            for this, we will have to pinpoint where the b'info' is in the raw file and then take everything after it.



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
        This is the tracker class. This class cosns
        """
        def __init__(self):
                self.generate_info_hash()


        def generate_info_hash(self,rawData):
                """
                This function is an attempt to create info hash without encoding the whole info_hash.

                for this, we will have to pinpoint where the b'info' is in the raw file and then take everything after it.
                """
                word = b'4:info'
                if rawData:
                        print("OK Now lets generate info hash using the alt trick.\n Checking where is 4:info.")
                # reason behind why 4:info, is because the translation of the word 'info' in bencode is '4:info'. SO yes, I predetermined it.
                try:
                        # lets try finding info from the main shit first.
                        position = rawData.index(word)+len(word)
                        
                        print("ok i found 4:info. now let's proceed.")
                except Exception as e:
                        print("No id didnt find.")

                temp_data = rawData[position:]
                level = 0
                end_offset = 0
                i = 0
                
                while i<len(temp_data):
                        char = temp_data[i:i+1]

                        if char == b'd' or char == b'l': # that means it is a dictionary or a list begining
                                level +=1
                        elif char == b'e':
                                level -=1       
                        elif char in b'0123456789':
                                colon_index = temp_data.find(b':',i) # i is the starting position for the search. We don't want to search the whole temp_data every time right so yeah
                                # colon index would give me the
                                if colon_index == -1: 
                                        raise ValueError("Corrupt")
                                str_len = int(len(temp_data[i:colon_index]) )
                            # Skip the length, the colon, and the string data itself.
                                i += (colon_index - i) + str_len
                        i += 1
                        if level == 0:
                                end_offset = i
                                break

            # If the level is 0, we've found the final closing 'e'.
                       
        
                if end_offset == 0:
                        raise ValueError("Could not determine the end of the info dictionary.")
            
                # Step 3: Slice the raw bytes.
                self.raw_info_bytes = temp_data[:end_offset]
                if self.raw_info_bytes: 
                        # print("I won brother I won, you lost. You lost you damn it you lost")
                        print("Info dictionary has been extracted.")
                self.info_hash = self.generate_hash()
                return self.info_hash
                
                
        
        def generate_hash(self):
                # SHA1 always makes 20Byte hashes
                return hashlib.sha1(self.raw_info_bytes).digest



