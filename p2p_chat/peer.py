import socket
import threading
import time
import uuid
import json
from pathlib import Path
from typing import Dict, Callable, Optional, List
from connection import Connection
from security.encryption import E2EEncryption


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
        
        # Initialize encryption
        self.encryption = E2EEncryption()
        
        # Message queue for offline messaging (store-and-forward)
        self.message_queue: Dict[str, List[dict]] = {}  # username -> [messages]
        self.group_message_queue: Dict[str, Dict[str, List[dict]]] = {}  # group_id -> {username -> [messages]}
        self._load_message_queue()
        
        print(f"🔐 Peer '{username}' initialized with E2E encryption")

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
            # Send handshake with public key
            try:
                conn.send_json({
                    "type": "hello",
                    "username": self.username,
                    "public_key": self.encryption.get_public_key_pem()
                })
            except Exception:
                pass

    def connect(self, host: str, port: int = 12345) -> Connection:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        conn = Connection(sock, addr=(host, port), on_message=self._on_message)
        key = f"{host}:{port}"
        with self._lock:
            self._connections[key] = conn
        # Send handshake with public key
        try:
            conn.send_json({
                "type": "hello",
                "username": self.username,
                "public_key": self.encryption.get_public_key_pem()
            })
        except Exception:
            pass
        return conn

    def _on_message(self, conn: Connection, message_obj: dict):
        """Handle incoming messages and route based on type"""
        msg_type = message_obj.get("type")
        
        if msg_type == "hello":
            # Handshake: learn the peer's username and public key
            peer_username = message_obj.get("username", "unknown")
            peer_public_key = message_obj.get("public_key")
            
            conn.username = peer_username
            with self._lock:
                self._connections_by_username[peer_username] = conn
            
            # Store peer's public key for encryption
            if peer_public_key:
                try:
                    self.encryption.add_peer_public_key(peer_username, peer_public_key)
                    print(f"🔑 Exchanged keys with {peer_username} - encryption ready")
                except Exception as e:
                    print(f"❌ Failed to store public key for {peer_username}: {e}")
            
            # Flush queued messages when peer connects
            self._flush_queued_messages(peer_username)
        
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
    
    def send_to(self, username: str, text: str) -> str:
        """
        Send a text message to a specific peer by username (encrypted if possible).
        
        Returns:
            "delivered" if sent successfully, "queued" if user offline, "failed" on error
        """
        # Try to encrypt the message
        if self.encryption.has_peer_key(username):
            try:
                encrypted_data = self.encryption.encrypt_message(username, text)
                message_obj = {
                    "type": "msg",
                    "from": self.username,
                    "timestamp": time.time(),
                    "encrypted": True,
                    "data": encrypted_data
                }
                print(f"🔒 Sending encrypted message to {username}")
            except Exception as e:
                print(f"⚠️ Encryption failed, sending plaintext: {e}")
                # Fallback to plaintext
                message_obj = {
                    "type": "msg",
                    "from": self.username,
                    "text": text,
                    "timestamp": time.time(),
                    "encrypted": False
                }
        else:
            # No public key yet, send plaintext
            print(f"⚠️ No encryption key for {username}, sending plaintext")
            message_obj = {
                "type": "msg",
                "from": self.username,
                "text": text,
                "timestamp": time.time(),
                "encrypted": False
            }
        
        with self._lock:
            conn = self._connections_by_username.get(username)
        
        if conn:
            try:
                conn.send_json(message_obj)
                return "delivered"  # Successfully sent
            except Exception as e:
                # Connection dead - remove and queue
                print(f"⚠️ Connection to {username} failed: {e}")
                with self._lock:
                    for key, c in list(self._connections.items()):
                        if c == conn:
                            del self._connections[key]
                            break
                    if username in self._connections_by_username:
                        del self._connections_by_username[username]
                
                # Queue the message
                self._queue_p2p_message(username, message_obj)
                return "queued"
        else:
            # No connection - queue the message
            self._queue_p2p_message(username, message_obj)
            return "queued"

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
        
        # Save message queue on shutdown
        self._save_message_queue()
    
    # ==================== OFFLINE MESSAGING (MESSAGE QUEUE) ====================
    
    def _get_queue_file(self) -> Path:
        """Get the message queue file path"""
        config_dir = Path.home() / ".p2p_chat"
        config_dir.mkdir(exist_ok=True)
        return config_dir / f"message_queue_{self.username}.json"
    
    def _load_message_queue(self):
        """Load message queue from disk"""
        queue_file = self._get_queue_file()
        if queue_file.exists():
            try:
                with open(queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.message_queue = data.get('p2p', {})
                    self.group_message_queue = data.get('group', {})
                    
                    # Count queued messages
                    p2p_count = sum(len(msgs) for msgs in self.message_queue.values())
                    group_count = sum(len(members) for group in self.group_message_queue.values() 
                                     for members in group.values())
                    
                    if p2p_count > 0 or group_count > 0:
                        print(f"📬 Loaded message queue: {p2p_count} P2P, {group_count} group messages")
            except Exception as e:
                print(f"⚠️ Failed to load message queue: {e}")
                self.message_queue = {}
                self.group_message_queue = {}
    
    def _save_message_queue(self):
        """Save message queue to disk"""
        queue_file = self._get_queue_file()
        try:
            data = {
                'p2p': self.message_queue,
                'group': self.group_message_queue
            }
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save message queue: {e}")
    
    def _queue_p2p_message(self, username: str, message_obj: dict):
        """Queue a P2P message for offline user"""
        if username not in self.message_queue:
            self.message_queue[username] = []
        
        self.message_queue[username].append(message_obj)
        self._save_message_queue()
        print(f"⏳ Queued P2P message for {username} (offline)")
    
    def _queue_group_message(self, group_id: str, username: str, message_obj: dict):
        """Queue a group message for offline user"""
        if group_id not in self.group_message_queue:
            self.group_message_queue[group_id] = {}
        
        if username not in self.group_message_queue[group_id]:
            self.group_message_queue[group_id][username] = []
        
        self.group_message_queue[group_id][username].append(message_obj)
        self._save_message_queue()
        print(f"⏳ Queued group message for {username} in {group_id} (offline)")
    
    def _flush_queued_messages(self, username: str):
        """Send all queued messages to a user who just came online"""
        # Flush P2P messages
        if username in self.message_queue and self.message_queue[username]:
            messages = self.message_queue[username]
            print(f"📤 Sending {len(messages)} queued P2P messages to {username}")
            
            sent_count = 0
            for msg in messages:
                try:
                    with self._lock:
                        conn = self._connections_by_username.get(username)
                    if conn:
                        conn.send_json(msg)
                        sent_count += 1
                    else:
                        break  # Connection lost
                except Exception as e:
                    print(f"⚠️ Failed to send queued message: {e}")
                    break
            
            # Remove sent messages
            if sent_count > 0:
                self.message_queue[username] = self.message_queue[username][sent_count:]
                if not self.message_queue[username]:
                    del self.message_queue[username]
                self._save_message_queue()
                print(f"✅ Sent {sent_count}/{len(messages)} queued P2P messages to {username}")
        
        # Flush group messages
        for group_id in list(self.group_message_queue.keys()):
            if username in self.group_message_queue[group_id]:
                messages = self.group_message_queue[group_id][username]
                print(f"📤 Sending {len(messages)} queued group messages to {username}")
                
                sent_count = 0
                for msg in messages:
                    try:
                        with self._lock:
                            conn = self._connections_by_username.get(username)
                        if conn:
                            conn.send_json(msg)
                            sent_count += 1
                        else:
                            break
                    except Exception as e:
                        print(f"⚠️ Failed to send queued group message: {e}")
                        break
                
                # Remove sent messages
                if sent_count > 0:
                    self.group_message_queue[group_id][username] = \
                        self.group_message_queue[group_id][username][sent_count:]
                    
                    if not self.group_message_queue[group_id][username]:
                        del self.group_message_queue[group_id][username]
                    
                    if not self.group_message_queue[group_id]:
                        del self.group_message_queue[group_id]
                    
                    self._save_message_queue()
                    print(f"✅ Sent {sent_count}/{len(messages)} queued group messages to {username}")
    
    # ==================== GROUP CHAT MESH NETWORKING ====================
    
    def create_group(self, group_id: str, member_usernames: List[str]) -> bytes:
        """
        Create a new group and generate encryption key.
        
        Args:
            group_id: Unique identifier for the group
            member_usernames: List of usernames in the group (including self)
            
        Returns:
            The generated group key (32 bytes)
        """
        # Generate group key
        group_key = self.encryption.create_group_key(group_id)
        
        # Send encrypted group key to all other members
        for member in member_usernames:
            if member != self.username:
                try:
                    encrypted_key = self.encryption.encrypt_group_key_for_member(group_key, member)
                    self.send_group_key(member, group_id, encrypted_key, member_usernames)
                except Exception as e:
                    print(f"⚠️ Failed to send group key to {member}: {e}")
        
        print(f"👥 Created group {group_id} with {len(member_usernames)} members")
        return group_key
    
    def send_group_key(self, username: str, group_id: str, encrypted_key: str, members: List[str]):
        """
        Send encrypted group key to a specific member.
        
        Args:
            username: Recipient username
            group_id: Group identifier
            encrypted_key: Base64-encoded encrypted group key
            members: List of all group members
        """
        message_obj = {
            "type": "group_key",
            "group_id": group_id,
            "encrypted_key": encrypted_key,
            "members": members,
            "from": self.username,
            "timestamp": time.time()
        }
        
        with self._lock:
            conn = self._connections_by_username.get(username)
        
        if conn:
            try:
                conn.send_json(message_obj)
                print(f"🔑 Sent group key for {group_id} to {username}")
            except Exception as e:
                print(f"❌ Failed to send group key to {username}: {e}")
        else:
            print(f"⚠️ Not connected to {username}, cannot send group key")
    
    def send_group_message(self, group_id: str, text: str, member_usernames: List[str]) -> Dict[str, int]:
        """
        Send a message to all members of a group (mesh broadcast).
        Uses TCP reliability - no ACKs needed. Queues messages for offline members.
        
        Args:
            group_id: Group identifier
            text: Message text (plaintext)
            member_usernames: List of all group members
            
        Returns:
            Dictionary with counts: {"delivered": N, "queued": M}
        """
        # Generate unique message ID
        msg_id = str(uuid.uuid4())
        
        # Encrypt message with group key
        try:
            encrypted_data = self.encryption.encrypt_group_message(group_id, text)
        except Exception as e:
            print(f"❌ Failed to encrypt group message: {e}")
            return {"delivered": 0, "queued": 0}
        
        message_obj = {
            "type": "group_msg",
            "group_id": group_id,
            "msg_id": msg_id,
            "from": self.username,
            "timestamp": time.time(),
            "encrypted_data": encrypted_data
        }
        
        # Send to all group members except self
        delivered_count = 0
        queued_count = 0
        
        for member in member_usernames:
            if member != self.username:
                with self._lock:
                    conn = self._connections_by_username.get(member)
                
                if conn:
                    try:
                        conn.send_json(message_obj)
                        delivered_count += 1
                    except Exception as e:
                        print(f"⚠️ Connection to {member} failed, queueing message")
                        # TCP connection failed - remove and queue
                        with self._lock:
                            for key, c in list(self._connections.items()):
                                if c == conn:
                                    del self._connections[key]
                                    break
                            if member in self._connections_by_username:
                                del self._connections_by_username[member]
                        
                        # Queue the message
                        self._queue_group_message(group_id, member, message_obj)
                        queued_count += 1
                else:
                    # No connection - queue the message
                    self._queue_group_message(group_id, member, message_obj)
                    queued_count += 1
        
        total_members = len(member_usernames) - 1  # Exclude self
        print(f"📤 Group message: {delivered_count} delivered, {queued_count} queued ({total_members} total)")
        
        return {"delivered": delivered_count, "queued": queued_count}
