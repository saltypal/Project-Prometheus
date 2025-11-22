"""Main window for P2P Chat application"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QTextEdit, QLineEdit, QPushButton,
                             QSplitter, QLabel, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.peers import PeerProfile
from models.messages import Message


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    send_message_signal = pyqtSignal(str, str)  # username, text
    connect_to_peer_signal = pyqtSignal(PeerProfile)  # profile
    
    def __init__(self):
        super().__init__()
        self.current_peer = None
        self.conversations = {}  # username -> list of Message objects
        
        self.setWindowTitle("P2P Chat")
        self.setGeometry(100, 100, 900, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main window UI"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Contacts list
        left_panel = self.create_contacts_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Chat area
        right_panel = self.create_chat_panel()
        splitter.addWidget(right_panel)
        
        # Set initial sizes (30% left, 70% right)
        splitter.setSizes([270, 630])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # Create menu bar
        self.create_menu_bar()
    
    def create_contacts_panel(self):
        """Create the left contacts panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Contacts")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.itemClicked.connect(self.on_contact_selected)
        layout.addWidget(self.contacts_list)
        
        # Add contact button
        add_contact_btn = QPushButton("+ Add Contact")
        add_contact_btn.clicked.connect(self.on_add_contact)
        layout.addWidget(add_contact_btn)
        
        panel.setLayout(layout)
        return panel
    
    def create_chat_panel(self):
        """Create the right chat panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Chat header
        self.chat_header = QLabel("Select a contact to start chatting")
        self.chat_header.setFont(QFont("Arial", 11, QFont.Bold))
        self.chat_header.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.chat_header)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 10))
        layout.addWidget(self.chat_display)
        
        # Message input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.on_send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send_message)
        self.send_btn.setEnabled(False)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        panel.setLayout(layout)
        return panel
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_action = file_menu.addAction("Add Contact")
        add_action.triggered.connect(self.on_add_contact)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
    
    def set_contacts(self, profiles):
        """Set the list of contacts"""
        self.contacts_list.clear()
        for profile in profiles:
            self.contacts_list.addItem(profile.username)
    
    def add_contact_to_list(self, profile: PeerProfile):
        """Add a single contact to the list"""
        self.contacts_list.addItem(profile.username)
    
    def on_contact_selected(self, item):
        """Handle contact selection"""
        username = item.text()
        self.current_peer = username
        self.chat_header.setText(f"Chat with {username}")
        self.send_btn.setEnabled(True)
        self.message_input.setEnabled(True)
        
        # Load conversation
        self.load_conversation(username)
        
        # Emit signal to connect if not already connected
        # Controller will handle this
    
    def on_add_contact(self):
        """Handle add contact button click"""
        from connect_dialog import ConnectDialog
        dialog = ConnectDialog(self)
        if dialog.exec_():
            profile = dialog.get_profile()
            if profile:
                # Signal will be handled by controller
                self.add_contact_to_list(profile)
                self.connect_to_peer_signal.emit(profile)
    
    def on_send_message(self):
        """Handle send message"""
        if not self.current_peer:
            return
        
        text = self.message_input.text().strip()
        if not text:
            return
        
        # Emit signal to send message
        self.send_message_signal.emit(self.current_peer, text)
        
        # Clear input
        self.message_input.clear()
    
    def add_message_to_display(self, sender: str, text: str, timestamp: float, is_own: bool = False):
        """Add a message to the chat display"""
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        
        if is_own:
            html = f'<p style="text-align: right; color: #0066cc;"><b>You</b> ({time_str})<br>{text}</p>'
        else:
            html = f'<p style="text-align: left; color: #006600;"><b>{sender}</b> ({time_str})<br>{text}</p>'
        
        self.chat_display.append(html)
    
    def load_conversation(self, username: str):
        """Load and display conversation history"""
        self.chat_display.clear()
        
        messages = self.conversations.get(username, [])
        for msg in messages:
            is_own = (msg.sender != username)
            self.add_message_to_display(msg.sender, msg.text, msg.timestamp, is_own)
    
    def add_message_to_conversation(self, username: str, message: Message):
        """Add a message to conversation history"""
        if username not in self.conversations:
            self.conversations[username] = []
        
        self.conversations[username].append(message)
        
        # Update display if this is the current conversation
        if self.current_peer == username:
            is_own = (message.sender != username)
            self.add_message_to_display(message.sender, message.text, message.timestamp, is_own)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About P2P Chat",
            "<h3>P2P Chat Application</h3>"
            "<p>A peer-to-peer chat application built with Python and PyQt5.</p>"
            "<p>Connect with friends directly without a central server.</p>"
        )
    
    def show_error(self, title: str, message: str):
        """Show an error message"""
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title: str, message: str):
        """Show an info message"""
        QMessageBox.information(self, title, message)
