import socket
import threading
import time
from typing import Dict, Callable, Optional
from connection import Connection


class Peer:
    """A simple peer that can accept incoming connections and connect to others.

    - start_listening(port)
    - connect(host, port)
    - broadcast(message)
    - send_to(username, text)
    - shutdown()
    """

    def __init__(self, username: str = "anonymous", on_message: Optional[Callable[[Connection, dict], None]] = None):
        self.username = username
        self.on_message = on_message
        self._server = None
        self._accept_thread = None
        self._connections: Dict[str, Connection] = {}  # key -> Connection
        self._connections_by_username: Dict[str, Connection] = {}  # username -> Connection
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def start_listening(self, host: str = '0.0.0.0', port: int = 12345):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((host, port))
        self._server.listen()
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                client_sock, addr = self._server.accept()
            except OSError:
                break
            conn = Connection(client_sock, addr=addr, on_message=self._on_message)
            key = f"{addr[0]}:{addr[1]}"
            with self._lock:
                self._connections[key] = conn
            # Send handshake
            try:
                conn.send_json({"type": "hello", "username": self.username})
            except Exception:
                pass

    def connect(self, host: str, port: int = 12345) -> Connection:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        conn = Connection(sock, addr=(host, port), on_message=self._on_message)
        key = f"{host}:{port}"
        with self._lock:
            self._connections[key] = conn
        # Send handshake
        try:
            conn.send_json({"type": "hello", "username": self.username})
        except Exception:
            pass
        return conn

    def _on_message(self, conn: Connection, message_obj: dict):
        """Handle incoming messages and route based on type"""
        msg_type = message_obj.get("type")
        
        if msg_type == "hello":
            # Handshake: learn the peer's username
            peer_username = message_obj.get("username", "unknown")
            conn.username = peer_username
            with self._lock:
                self._connections_by_username[peer_username] = conn
        
        # Forward all messages to the user callback
        if self.on_message:
            self.on_message(conn, message_obj)

    def broadcast(self, text: str):
        """Broadcast a text message to all connected peers"""
        message_obj = {
            "type": "msg",
            "from": self.username,
            "text": text,
            "timestamp": time.time()
        }
        with self._lock:
            conns = list(self._connections.items())

        for key, conn in conns:
            try:
                conn.send_json(message_obj)
            except Exception:
                # remove dead connections
                with self._lock:
                    if key in self._connections:
                        del self._connections[key]
                    if conn.username and conn.username in self._connections_by_username:
                        del self._connections_by_username[conn.username]
    
    def send_to(self, username: str, text: str):
        """Send a text message to a specific peer by username"""
        message_obj = {
            "type": "msg",
            "from": self.username,
            "text": text,
            "timestamp": time.time()
        }
        with self._lock:
            conn = self._connections_by_username.get(username)
        
        if conn:
            try:
                conn.send_json(message_obj)
            except Exception:
                # remove dead connection
                with self._lock:
                    for key, c in list(self._connections.items()):
                        if c == conn:
                            del self._connections[key]
                            break
                    if username in self._connections_by_username:
                        del self._connections_by_username[username]
                raise
        else:
            raise ValueError(f"No connection to user '{username}'")

    def close_connection(self, key: str):
        with self._lock:
            conn = self._connections.pop(key, None)
        if conn:
            conn.close()

    def list_peers(self):
        with self._lock:
            return list(self._connections.keys())

    def get_connected_usernames(self):
        """Get list of currently connected peer usernames"""
        with self._lock:
            return list(self._connections_by_username.keys())

    def shutdown(self):
        self._stop.set()
        try:
            if self._server:
                self._server.close()
        except Exception:
            pass
        with self._lock:
            conns = list(self._connections.values())
            self._connections.clear()
            self._connections_by_username.clear()
        for c in conns:
            c.close()
