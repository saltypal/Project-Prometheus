"""Controller to bridge network events and GUI"""

from PyQt5.QtCore import QObject, pyqtSignal
import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from peer import Peer
from models.peers import PeerProfile
from models.messages import Message
from storage import load_profiles, save_profiles


class NetworkSignals(QObject):
    """Qt signals for network events (thread-safe communication with GUI)"""
    message_received = pyqtSignal(str, Message)  # username, message
    peer_connected = pyqtSignal(str)  # username
    peer_disconnected = pyqtSignal(str)  # username
    connection_error = pyqtSignal(str, str)  # username, error_message


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
        self.signals.connection_error.connect(self.on_connection_error_gui)
        
        # GUI signals -> Controller
        self.main_window.send_message_signal.connect(self.send_message)
        self.main_window.connect_to_peer_signal.connect(self.connect_to_peer)
    
    def load_profiles(self):
        """Load saved peer profiles"""
        profiles_list = load_profiles()
        for profile in profiles_list:
            self.profiles[profile.username] = profile
        
        self.main_window.set_contacts(profiles_list)
    
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
            # Send via network
            self.peer.send_to(username, text)
            
            # Create message object
            message = Message(
                sender=self.username,
                receiver=username,
                text=text,
                timestamp=time.time()
            )
            
            # Add to GUI conversation
            self.main_window.add_message_to_conversation(username, message)
            
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
            # Chat message
            sender = message_obj.get("from", "unknown")
            text = message_obj.get("text", "")
            timestamp = message_obj.get("timestamp", time.time())
            
            # Create message object
            message = Message(
                sender=sender,
                receiver=self.username,
                text=text,
                timestamp=timestamp
            )
            
            # Emit signal to update GUI (thread-safe)
            self.signals.message_received.emit(sender, message)
    
    def on_message_received_gui(self, username: str, message: Message):
        """Handle received message in GUI thread"""
        # Add sender to contacts if not already there
        if username not in self.profiles:
            # Auto-add new contact (we don't know their IP from here, they connected to us)
            # Just add to conversation, user can manually add them later if needed
            pass
        
        # Add message to conversation
        self.main_window.add_message_to_conversation(username, message)
        
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
    
    def shutdown(self):
        """Cleanup on shutdown"""
        self.peer.shutdown()
