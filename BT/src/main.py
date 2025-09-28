from client import client_Info
from bencoding import benDecode

class bitTorrent_client:
    def __init__(self):
        client_metadata = client_Info()
        sourceFile = self.bendecode_torrent_file()

    def bendecode_torrent_file():
        """
        This will load get the benDecoded data. It will also return the name of the file.
    
        """

        try:
          
            benDecoder = benDecode(torrent_file_path)
            benDecoded_data = benDecoder.deBencode_list()
            benDecoder.write_to_file(benDecoded_data)
            # we also need to return the name of the file. like the name of the decoded file.
        except Exception as e:
            print(f"\nerrorrrrrrrr {e}")

    def getTorrentFileName():
        """
        tis function will return file name and all. it will basically load the file into the working directory of the 
        
        """