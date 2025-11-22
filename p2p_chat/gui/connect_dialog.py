"""Connect dialog for adding/editing peer contacts"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.peers import PeerProfile


class ConnectDialog(QDialog):
    """Dialog for adding or editing a peer contact"""
    
    def __init__(self, parent=None, profile: PeerProfile = None):
        super().__init__(parent)
        self.profile = profile
        self.result_profile = None
        
        self.setWindowTitle("Add Contact" if profile is None else "Edit Contact")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.setup_ui()
        
        if profile:
            self.load_profile(profile)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Username field
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter peer's username")
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Host field
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("IP Address:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g., 192.168.1.100")
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)
        
        # Port field
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("e.g., 12345")
        self.port_input.setText("12345")
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept_dialog)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_profile(self, profile: PeerProfile):
        """Load an existing profile into the form"""
        self.username_input.setText(profile.username)
        self.host_input.setText(profile.host)
        self.port_input.setText(str(profile.port))
    
    def accept_dialog(self):
        """Validate and accept the dialog"""
        username = self.username_input.text().strip()
        host = self.host_input.text().strip()
        port_text = self.port_input.text().strip()
        
        # Validate inputs
        if not username:
            QMessageBox.warning(self, "Invalid Input", "Username cannot be empty")
            return
        
        if not host:
            QMessageBox.warning(self, "Invalid Input", "IP address cannot be empty")
            return
        
        try:
            port = int(port_text)
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Port must be a number between 1 and 65535")
            return
        
        # Create profile and accept
        self.result_profile = PeerProfile(username=username, host=host, port=port)
        self.accept()
    
    def get_profile(self) -> PeerProfile:
        """Get the resulting profile after dialog is accepted"""
        return self.result_profile
