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
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)
        
        self.apply_stylesheet()
        self.setup_ui()
        
        if profile:
            self.load_profile(profile)
    
    def get_message_box_stylesheet(self):
        """Get stylesheet for message boxes"""
        return """
            QMessageBox {
                background-color: #2b2b40;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 14px;
                background: transparent;
            }
            QMessageBox QPushButton {
                background-color: #5865f2;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 9px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
                min-height: 36px;
            }
            QMessageBox QPushButton:hover {
                background-color: #6975ff;
            }
            QMessageBox QPushButton:pressed {
                background-color: #4752c4;
            }
        """
    
    def apply_stylesheet(self):
        """Apply maximum clarity stylesheet matching main window"""
        self.setStyleSheet("""
            * {
                font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
            }
            QDialog {
                background-color: #2b2b40;
            }
            QLabel {
                font-size: 16px;
                color: #ffffff;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #1e1e2e;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                color: #ffffff;
                selection-background-color: #5865f2;
                selection-color: white;
                min-height: 36px;
            }
            QLineEdit:focus {
                border: 1px solid #5865f2;
                background-color: #36364d;
            }
            QPushButton {
                background-color: #5865f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #6975ff;
            }
            QPushButton:pressed {
                background-color: #4752c4;
            }
            QPushButton#cancelButton {
                background-color: #3d3d5c;
                color: #ffffff;
            }
            QPushButton#cancelButton:hover {
                background-color: #4e4e6b;
                box-shadow: 0 4px 12px rgba(61, 61, 92, 0.4);
            }
        """)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Add New Contact" if self.profile is None else "Edit Contact")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: 700; 
            color: #ffffff; 
            padding: 10px 0;
        """)
        layout.addWidget(title)
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(5)
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter peer's username")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Host field
        host_layout = QVBoxLayout()
        host_layout.setSpacing(5)
        host_label = QLabel("IP Address:")
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g., 192.168.1.100 or domain.com")
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)
        
        # Port field
        port_layout = QVBoxLayout()
        port_layout.setSpacing(5)
        port_label = QLabel("Port:")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Default: 12345")
        self.port_input.setText("12345")
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Save" if self.profile else "Add")
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
            msg = QMessageBox(self)
            msg.setStyleSheet(self.get_message_box_stylesheet())
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid Input")
            msg.setText("Username cannot be empty")
            msg.exec_()
            return
        
        if not host:
            msg = QMessageBox(self)
            msg.setStyleSheet(self.get_message_box_stylesheet())
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid Input")
            msg.setText("IP address cannot be empty")
            msg.exec_()
            return
        
        try:
            port = int(port_text)
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            msg = QMessageBox(self)
            msg.setStyleSheet(self.get_message_box_stylesheet())
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid Input")
            msg.setText("Port must be a number between 1 and 65535")
            msg.exec_()
            return
        
        # Create profile and accept
        self.result_profile = PeerProfile(username=username, host=host, port=port)
        self.accept()
    
    def get_profile(self) -> PeerProfile:
        """Get the resulting profile after dialog is accepted"""
        return self.result_profile
