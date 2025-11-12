import socket
import threading
from typing import Dict, Callable, Optional
from connection import Connection


class Peer:
    """A simple peer that can accept incoming connections and connect to others.

    - start_listening(port)
    - connect(host, port)
    - broadcast(message)
    - shutdown()
    """

    def __init__(self, on_message: Optional[Callable[[Connection, str], None]] = None):
        self.on_message = on_message
        self._server = None
        self._accept_thread = None
        self._connections: Dict[str, Connection] = {}
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

    def connect(self, host: str, port: int = 12345) -> Connection:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        conn = Connection(sock, addr=(host, port), on_message=self._on_message)
        key = f"{host}:{port}"
        with self._lock:
            self._connections[key] = conn
        return conn

    def _on_message(self, conn: Connection, text: str):
        if self.on_message:
            self.on_message(conn, text)

    def broadcast(self, text: str):
        with self._lock:
            conns = list(self._connections.items())

        for key, conn in conns:
            try:
                conn.send(text)
            except Exception:
                # remove dead connections
                with self._lock:
                    if key in self._connections:
                        del self._connections[key]

    def close_connection(self, key: str):
        with self._lock:
            conn = self._connections.pop(key, None)
        if conn:
            conn.close()

    def list_peers(self):
        with self._lock:
            return list(self._connections.keys())

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
        for c in conns:
            c.close()
