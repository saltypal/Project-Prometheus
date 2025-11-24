import random
"""
MADE BY SATYA PALADUGU AT 28/9/2025 7:40 PM

This file deals only with generating A peer ID for a particular Session.
"""
class client_Info:
    """
    This Class deals with information which is unique to the client as a whole.
        - Peer_ID
        - PORT Number
    
    """

    def __init__(self):
        self.peerID = self.generateID() 
        self.portNumber = self.generatePortNumber()


    def generateID(self):
        """
            This function deals with generating a peerID for the entire Client.
            Each BitTorrent client is identified by a string called Peer ID. This ID is sometimes used by trackers to whitelist only a limited amount of trusted clients. The size of the Peer ID field is 20 bytes.
            qBittorrent Peer ID is formatted as follows: -qBXYZ0-<12 random bytes> Where:       
            our id format:
              PAL000-<12 random bytes>
        """
        clientName = b'-SALPAL-'
        # x = bytes(str(random.randint(100000000000,999999999999)).encode('utf-8'))
        """The bytes you're actually getting are the ASCII codes for the characters '1', '2', '3', etc. 
        These are not truly random bytes. A truly random byte can be any value from 0 to 255 (\x00 to \xff).
        Your method only generates bytes from the small set of numbers that represent digits"""
        
        otherBytes = bytes(random.randint(0,255) for z in range(12))
        peerID = clientName+otherBytes
        print(f"------\n Peer ID Generated: {peerID}\n------")
        return peerID

    def generatePortNumber(self):
        """
            This function is to allocate for use and return a portnumber for the client.
        """

        self.portNumber = 6882
        print(f"------\nPort Number Generated: {self.portNumber}\n------")

        return self.portNumber
    
    # Getters
    def get_peerID(self):
        return self.peerID

    def get_portNumber(self)       :
        return self.portNumber
