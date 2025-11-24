import socket
import threading
from peer2peer import PeerConnection

"""
MADE BY SATYA PALADUGU
Option A: The Server Socket.
Listens for incoming connections and spawns Peer threads.
"""

class Server(threading.Thread):
    def __init__(self, port, info_hash, peer_id, piece_manager):
        threading.Thread.__init__(self)
        self.port = port
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        self.running = False

    def run(self):
        """
        The Main Server Loop.
        """
        self.running = True
        try:
            # 0.0.0.0 means "Listen on all network interfaces"
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(('0.0.0.0', self.port))
            self.sock.listen(5) # Backlog of 5 connections
            
            print(f"Server listening on 0.0.0.0:{self.port}")
            
            while self.running:
                # Accept new connection
                client_sock, addr = self.sock.accept()
                
                # Spawn a worker thread
                peer = PeerConnection(
                    piece_manager=self.piece_manager,
                    info_hash=self.info_hash,
                    peer_id=self.peer_id,
                    sock=client_sock
                )
                peer.start()
                
        except Exception as e:
            print(f"Server Crashed: {e}")
        finally:
            self.sock.close()