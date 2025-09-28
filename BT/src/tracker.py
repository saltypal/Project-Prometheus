"""

MADE BY SATYA PALADUGU AT 28/9/2025 2:40 PM

        
This file deals with:
1. info_hash
2. Request generation for HTTP and UDP trackers.
3. Response acceptance
4. 


key parameters your client must include in the request:
info_hash: This is a 20-byte SHA1 hash of the bencoded info dictionary from the torrent file. This hash uniquely identifies the torrent on the network.
peer_id: A unique 20-byte ID for your client. You can generate this randomly.
port: The port number your client is listening on for incoming peer connections. Common ports are 6881-6889, but you can choose any available port.
uploaded: The total amount of data you've uploaded in bytes. Starts at 0.
downloaded: The total amount of data you've downloaded in bytes. Starts at 0.
left: The number of bytes remaining to be downloaded.
event: This parameter tells the tracker what's happening. The most common events are:
        started: Sent when your client first begins downloading.
        completed: Sent when you finish downloading the file.
        stopped: Sent when you close the client.
        (No event): Sent for periodic updates while downloading.


"""



