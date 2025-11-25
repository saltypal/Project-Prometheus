"""Group creation dialog for creating new group chats"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QListWidget,
                             QListWidgetItem, QCheckBox)
from PyQt5.QtCore import Qt
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class GroupDialog(QDialog):
    """Dialog for creating a new group chat"""
    
    def __init__(self, parent=None, available_contacts=None):
        super().__init__(parent)
        self.available_contacts = available_contacts or []  # List of PeerProfile objects
        self.selected_members = []
        self.group_name = None
        
        self.setWindowTitle("Create Space")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(550)
        
        self.apply_stylesheet()
        self.setup_ui()
    
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
            QLabel#titleLabel {
                font-size: 18px; 
                font-weight: 700; 
                color: #ffffff; 
                padding: 10px 0;
            }
            QLabel#sectionLabel {
                font-size: 13px;
                font-weight: 600;
                color: #b9bbbe;
                padding: 8px 0px 4px 0px;
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
            QListWidget {
                background-color: #1e1e2e;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px 0px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3d3d5c;
            }
            QCheckBox {
                font-size: 16px;
                color: #ffffff;
                spacing: 12px;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #3d3d5c;
                background-color: #1e1e2e;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #5865f2;
                background-color: #36364d;
            }
            QCheckBox::indicator:checked {
                background-color: #5865f2;
                border: 2px solid #5865f2;
                image: url(none);
            }
            QPushButton {
                background-color: #5865f2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 110px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #6975ff;
            }
            QPushButton:pressed {
                background-color: #4752c4;
            }
            QPushButton:disabled {
                background-color: #3d3d5c;
                color: #6e6e89;
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
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Create New Space")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        # Group name section
        name_label = QLabel("Space Name")
        name_label.setObjectName("sectionLabel")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter space name (e.g., Study Space)")
        self.name_input.textChanged.connect(self.update_selected_count)
        layout.addWidget(self.name_input)
        
        layout.addSpacing(10)
        
        # Members selection section
        members_label = QLabel(f"Select Members ({len(self.available_contacts)} available)")
        members_label.setObjectName("sectionLabel")
        layout.addWidget(members_label)
        
        # Member list with checkboxes
        self.member_list = QListWidget()
        self.member_list.setSelectionMode(QListWidget.NoSelection)
        
        # Add contacts as checkable items
        for contact in self.available_contacts:
            item = QListWidgetItem(self.member_list)
            checkbox = QCheckBox(f"{contact.username} ({contact.host}:{contact.port})")
            checkbox.setProperty("username", contact.username)
            checkbox.stateChanged.connect(self.update_selected_count)
            self.member_list.addItem(item)
            self.member_list.setItemWidget(item, checkbox)
        
        layout.addWidget(self.member_list)
        
        # Selected count
        self.count_label = QLabel("Selected: 0 members")
        self.count_label.setStyleSheet("font-size: 12px; color: #b9bbbe; padding: 4px 0; font-weight: 600;")
        layout.addWidget(self.count_label)
        
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create Space")
        self.create_btn.setDefault(True)
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self.accept_dialog)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_selected_count(self):
        """Update the selected members count"""
        count = 0
        for i in range(self.member_list.count()):
            item = self.member_list.item(i)
            checkbox = self.member_list.itemWidget(item)
            if checkbox and checkbox.isChecked():
                count += 1
        
        self.count_label.setText(f"Selected: {count} member(s)")
        if count >= 2:
            self.count_label.setStyleSheet("font-size: 12px; color: #57f287; padding: 4px 0; font-weight: 600;")
        else:
            self.count_label.setStyleSheet("font-size: 12px; color: #b9bbbe; padding: 4px 0; font-weight: 600;")
        
        # Enable create button only if at least 2 members selected and name is provided
        self.create_btn.setEnabled(count >= 2 and len(self.name_input.text().strip()) > 0)
    
    def accept_dialog(self):
        """Validate and accept the dialog"""
        self.group_name = self.name_input.text().strip()
        
        if not self.group_name:
            msg = QMessageBox(self)
            msg.setStyleSheet(self.get_message_box_stylesheet())
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid Input")
            msg.setText("Space name cannot be empty")
            msg.exec_()
            return
        
        # Get selected members
        self.selected_members = []
        for i in range(self.member_list.count()):
            item = self.member_list.item(i)
            checkbox = self.member_list.itemWidget(item)
            if checkbox and checkbox.isChecked():
                username = checkbox.property("username")
                self.selected_members.append(username)
        
        if len(self.selected_members) < 2:
            msg = QMessageBox(self)
            msg.setStyleSheet(self.get_message_box_stylesheet())
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid Selection")
            msg.setText("Please select at least 2 members for the space")
            msg.exec_()
            return
        
        self.accept()
    
    def get_group_data(self):
        """Get the resulting group data after dialog is accepted"""
        return {
            'name': self.group_name,
            'members': self.selected_members
        }
