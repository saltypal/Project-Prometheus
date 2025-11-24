"""Controller to bridge network events and GUI"""

from PyQt5.QtCore import QObject, pyqtSignal
import sys
from pathlib import Path
import time
import uuid

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from peer import Peer
from models.peers import PeerProfile
from models.messages import Message
from models.groups import Group, GroupMessage
from storage import load_profiles, save_profiles
from storage.database import ChatDatabase
from storage.groups import load_groups, save_groups, add_group, get_group


class NetworkSignals(QObject):
    """Qt signals for network events (thread-safe communication with GUI)"""
    message_received = pyqtSignal(str, Message)  # username, message
    group_message_received = pyqtSignal(str, GroupMessage)  # group_id, message
    peer_connected = pyqtSignal(str)  # username
    peer_disconnected = pyqtSignal(str)  # username
    connection_error = pyqtSignal(str, str)  # username, error_message
    group_key_received = pyqtSignal(str, list)  # group_id, members


class ChatController:
    """Controller that manages the connection between network and GUI"""
    
    def __init__(self, main_window, username: str, listen_port: int = 12345):
        self.main_window = main_window
        self.username = username
        self.listen_port = listen_port
        
        # Network signals
        self.signals = NetworkSignals()
        
        # Peer profiles
        self.profiles = {}  # username -> PeerProfile
        
        # Groups
        self.groups = {}  # group_id -> Group
        
        # Database for message history
        self.db = ChatDatabase()
        
        # Create peer
        self.peer = Peer(username=username, on_message=self.on_network_message)
        
        # Connect signals to GUI slots
        self.connect_signals()
        
        # Start listening
        try:
            self.peer.start_listening(port=listen_port)
            print(f"Listening on port {listen_port}")
        except Exception as e:
            print(f"Failed to start listening: {e}")
            self.main_window.show_error("Network Error", f"Failed to start listening on port {listen_port}: {e}")
    
    def connect_signals(self):
        """Connect Qt signals to slots"""
        # Network signals -> GUI
        self.signals.message_received.connect(self.on_message_received_gui)
        self.signals.group_message_received.connect(self.on_group_message_received_gui)
        self.signals.connection_error.connect(self.on_connection_error_gui)
        self.signals.group_key_received.connect(self.on_group_key_received_gui)
        
        # GUI signals -> Controller
        self.main_window.send_message_signal.connect(self.send_message)
        self.main_window.send_group_message_signal.connect(self.send_group_message)
        self.main_window.connect_to_peer_signal.connect(self.connect_to_peer)
        self.main_window.delete_contact_signal.connect(self.on_delete_contact)
        self.main_window.edit_contact_signal.connect(self.on_edit_contact)
        self.main_window.create_group_signal.connect(self.create_group)
    
    def load_profiles(self):
        """Load saved peer profiles and groups"""
        # Load contacts
        profiles_list = load_profiles()
        for profile in profiles_list:
            self.profiles[profile.username] = profile
        
        self.main_window.set_contacts(profiles_list)
        
        # Load chat history for each profile
        for profile in profiles_list:
            messages = self.db.get_conversation(self.username, profile.username)
            for message in messages:
                self.main_window.add_message_to_conversation(profile.username, message, save_to_db=False)
        
        # Load groups
        self.load_groups()
        for group in self.groups.values():
            self.main_window.add_group_to_list(group)
            
            # Load group chat history
            group_messages = self.db.get_group_conversation(group.group_id)
            for msg in group_messages:
                self.main_window.add_group_message_to_conversation(group.group_id, msg)
    
    def save_profile(self, profile: PeerProfile):
        """Save a new or updated profile"""
        self.profiles[profile.username] = profile
        save_profiles(list(self.profiles.values()))
    
    def connect_to_peer(self, profile: PeerProfile):
        """Connect to a peer"""
        try:
            # Save profile
            self.save_profile(profile)
            
            # Try to connect
            self.peer.connect(profile.host, profile.port)
            print(f"Connected to {profile.username} at {profile.host}:{profile.port}")
            
        except Exception as e:
            print(f"Failed to connect to {profile.username}: {e}")
            self.signals.connection_error.emit(profile.username, str(e))
    
    def send_message(self, username: str, text: str):
        """Send a message to a peer"""
        try:
            # Send via network (returns status: "delivered" or "queued")
            status = self.peer.send_to(username, text)
            
            # Create message object with status
            message = Message(
                sender=self.username,
                receiver=username,
                text=text,
                timestamp=time.time(),
                status=status
            )
            
            # Save to database
            self.db.save_message(message, is_outgoing=True)
            
            # Add to GUI conversation
            self.main_window.add_message_to_conversation(username, message, save_to_db=False)
            
            # Show status feedback
            if status == "queued":
                print(f"⏳ Message queued for {username} (offline)")
            
        except Exception as e:
            print(f"Failed to send message to {username}: {e}")
            self.signals.connection_error.emit(username, str(e))
    
    def on_network_message(self, conn, message_obj: dict):
        """Handle incoming network messages (called from network thread)"""
        msg_type = message_obj.get("type")
        
        if msg_type == "hello":
            # Handshake message
            peer_username = message_obj.get("username", "unknown")
            print(f"Received hello from {peer_username}")
            self.signals.peer_connected.emit(peer_username)
            
        elif msg_type == "msg":
            # Chat message - may be encrypted
            sender = message_obj.get("from", "unknown")
            timestamp = message_obj.get("timestamp", time.time())
            is_encrypted = message_obj.get("encrypted", False)
            
            # Decrypt if encrypted
            if is_encrypted:
                try:
                    encrypted_data = message_obj.get("data", {})
                    text = self.peer.encryption.decrypt_message(encrypted_data)
                    print(f"🔓 Decrypted message from {sender}")
                except Exception as e:
                    print(f"❌ Failed to decrypt message from {sender}: {e}")
                    text = "[Encrypted message - decryption failed]"
            else:
                text = message_obj.get("text", "")
                print(f"⚠️ Received unencrypted message from {sender}")
            
            # Create message object
            message = Message(
                sender=sender,
                receiver=self.username,
                text=text,
                timestamp=timestamp
            )
            
            # Emit signal to update GUI (thread-safe)
            self.signals.message_received.emit(sender, message)
        
        elif msg_type == "group_key":
            # Group key distribution
            group_id = message_obj.get("group_id")
            encrypted_key = message_obj.get("encrypted_key")
            members = message_obj.get("members", [])
            sender = message_obj.get("from", "unknown")
            
            try:
                # Decrypt the group key with our RSA private key
                group_key = self.peer.encryption.decrypt_group_key(encrypted_key)
                
                # Add to encryption module
                self.peer.encryption.add_group_key(group_id, group_key)
                
                # Save group info
                group = Group(
                    group_id=group_id,
                    name=f"Group with {', '.join(members[:3])}{'...' if len(members) > 3 else ''}",
                    members=members,
                    creator=sender,
                    group_key=encrypted_key  # Store encrypted version
                )
                self.groups[group_id] = group
                add_group(group)
                
                print(f"🔑 Received and stored group key for {group_id}")
                
                # Emit signal for GUI
                self.signals.group_key_received.emit(group_id, members)
                
            except Exception as e:
                print(f"❌ Failed to process group key: {e}")
        
        elif msg_type == "group_msg":
            # Group message
            group_id = message_obj.get("group_id")
            sender = message_obj.get("from", "unknown")
            timestamp = message_obj.get("timestamp", time.time())
            encrypted_data = message_obj.get("encrypted_data", {})
            msg_id = message_obj.get("msg_id")
            
            try:
                # Decrypt with group key
                text = self.peer.encryption.decrypt_group_message(group_id, encrypted_data)
                print(f"🔓 Decrypted group message from {sender} in {group_id}")
                
                # Create group message object
                group_message = GroupMessage(
                    group_id=group_id,
                    from_user=sender,
                    text=text,
                    timestamp=timestamp,
                    msg_id=msg_id
                )
                
                # Emit signal to update GUI
                self.signals.group_message_received.emit(group_id, group_message)
                
            except Exception as e:
                print(f"❌ Failed to decrypt group message: {e}")
    
    def on_message_received_gui(self, username: str, message: Message):
        """Handle received message in GUI thread"""
        # Add sender to contacts if not already there
        if username not in self.profiles:
            # Auto-add new contact (we don't know their IP from here, they connected to us)
            # Just add to conversation, user can manually add them later if needed
            pass
        
        # Save to database
        self.db.save_message(message, is_outgoing=False)
        
        # Add message to conversation
        self.main_window.add_message_to_conversation(username, message, save_to_db=False)
        
        # If sender is not in contacts list, add them
        contacts = [self.main_window.contacts_list.item(i).text() 
                   for i in range(self.main_window.contacts_list.count())]
        if username not in contacts:
            self.main_window.add_contact_to_list(PeerProfile(username, "unknown", 0))
    
    def on_connection_error_gui(self, username: str, error_message: str):
        """Handle connection error in GUI thread"""
        self.main_window.show_error(
            "Connection Error",
            f"Failed to communicate with {username}:\n{error_message}"
        )
    
    def on_group_message_received_gui(self, group_id: str, message: GroupMessage):
        """Handle received group message in GUI thread"""
        # Save to database
        self.db.save_group_message(message)
        
        # Add to GUI conversation
        self.main_window.add_group_message_to_conversation(group_id, message)
        
        print(f"📨 Received group message in {group_id} from {message.from_user}")
    
    def on_group_key_received_gui(self, group_id: str, members: list):
        """Handle group key received event in GUI thread"""
        # Group was created or we joined, update UI
        group = self.groups.get(group_id)
        if group:
            self.main_window.add_group_to_list(group)
            print(f"🔑 Received key for group: {group.name}")
    
    def on_delete_contact(self, username: str):
        """Handle contact deletion from GUI"""
        # Delete from profiles
        if username in self.profiles:
            del self.profiles[username]
            save_profiles(list(self.profiles.values()))
        
        # Delete chat history
        self.db.delete_conversation(self.username, username)
    
    def on_edit_contact(self, profile: PeerProfile):
        """Handle contact edit from GUI"""
        self.save_profile(profile)
    
    # ==================== GROUP CHAT METHODS ====================
    
    def create_group(self, group_name: str, member_usernames: list):
        """
        Create a new group chat.
        
        Args:
            group_name: Display name for the group
            member_usernames: List of usernames to include (should include self)
        """
        # Generate unique group ID
        group_id = str(uuid.uuid4())
        
        # Ensure we're in the members list
        if self.username not in member_usernames:
            member_usernames.append(self.username)
        
        # Create group in peer layer (generates and distributes key)
        try:
            group_key = self.peer.create_group(group_id, member_usernames)
            
            # Create group object
            group = Group(
                group_id=group_id,
                name=group_name,
                members=member_usernames,
                creator=self.username
            )
            
            # Store locally
            self.groups[group_id] = group
            add_group(group)
            
            # Add to GUI
            self.main_window.add_group_to_list(group)
            
            print(f"👥 Created group '{group_name}' with {len(member_usernames)} members")
            self.main_window.show_info("Group Created", f"Group '{group_name}' created successfully!")
            return group
            
        except Exception as e:
            print(f"❌ Failed to create group: {e}")
            raise
    
    def send_group_message(self, group_id: str, text: str):
        """
        Send a message to a group (mesh broadcast to all members).
        
        Args:
            group_id: Group identifier
            text: Message text
        """
        # Get group
        group = self.groups.get(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        try:
            # Send via peer layer (mesh broadcast) - returns delivery status
            delivery_status = self.peer.send_group_message(group_id, text, group.members)
            
            # Determine overall status
            if delivery_status["queued"] > 0:
                status = "queued"  # Some messages queued
            elif delivery_status["delivered"] > 0:
                status = "delivered"  # All delivered
            else:
                status = "failed"  # None sent
            
            # Create message object for our own view
            message = GroupMessage(
                group_id=group_id,
                from_user=self.username,
                text=text,
                timestamp=time.time(),
                msg_id=str(uuid.uuid4()),
                status=status
            )
            
            # Save to database
            self.db.save_group_message(message)
            
            # Add to GUI
            self.main_window.add_group_message_to_conversation(group_id, message)
            
            # Show status feedback
            if delivery_status["queued"] > 0:
                print(f"⏳ {delivery_status['queued']} member(s) offline - messages queued")
            
            print(f"📤 Sent message to group {group.name}")
            
        except Exception as e:
            print(f"❌ Failed to send group message: {e}")
            raise
    
    def load_groups(self):
        """Load saved groups from storage"""
        groups_list = load_groups()
        for group in groups_list:
            self.groups[group.group_id] = group
            
            # If we have an encrypted group key stored, decrypt it
            if group.group_key:
                try:
                    group_key = self.peer.encryption.decrypt_group_key(group.group_key)
                    self.peer.encryption.add_group_key(group.group_id, group_key)
                except Exception as e:
                    print(f"⚠️ Failed to load key for group {group.name}: {e}")
        
        print(f"📚 Loaded {len(groups_list)} groups")
    
    def shutdown(self):
        """Cleanup on shutdown"""
        self.db.close()
        self.peer.shutdown()
