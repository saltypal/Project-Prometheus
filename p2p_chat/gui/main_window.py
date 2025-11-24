"""Main window for P2P Chat application"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QTextEdit, QLineEdit, QPushButton,
                             QSplitter, QLabel, QMessageBox, QInputDialog,
                             QToolBar, QAction, QListWidgetItem, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QFont, QIcon
import sys
from pathlib import Path
from datetime import datetime
import json
from bittorrent_integration import BitTorrentManager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.peers import PeerProfile
from models.messages import Message
from models.groups import Group, GroupMessage
from gui.group_dialog import GroupDialog


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    send_message_signal = pyqtSignal(str, str)  # username, text
    connect_to_peer_signal = pyqtSignal(PeerProfile)  # profile
    delete_contact_signal = pyqtSignal(str)  # username
    edit_contact_signal = pyqtSignal(PeerProfile)  # profile
    create_group_signal = pyqtSignal(str, list)  # group_name, members
    send_group_message_signal = pyqtSignal(str, str)  # group_id, text
    
    def __init__(self):
        super().__init__()
        self.current_peer = None
        self.current_group = None
        self.view_mode = "contact"  # "contact" or "group"
        self.conversations = {}  # username -> list of Message objects
        self.group_conversations = {}  # group_id -> list of GroupMessage objects
        self.profile_map = {}  # username -> PeerProfile
        self.groups = {}  # group_id -> Group
        
        # Initialize BitTorrent Manager
        self.bt_manager = BitTorrentManager()
        
        self.setWindowTitle("P2P Chat")
        self.setGeometry(100, 100, 1000, 700)
        
        # Apply modern stylesheet
        self.apply_stylesheet()
        
        self.setup_ui()
    
    def get_avatar_color(self, username):
        """Generate a consistent color for a username"""
        colors = [
            '#5865f2', '#57f287', '#faa61a', '#ed4245',
            '#eb459e', '#9b59b6', '#3498db', '#1abc9c',
            '#f39c12', '#e74c3c', '#e67e22', '#16a085'
        ]
        hash_value = sum(ord(c) for c in username)
        return colors[hash_value % len(colors)]
    
    def get_initials(self, username):
        """Get initials from username"""
        parts = username.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return username[:2].upper() if len(username) >= 2 else username.upper()
    
    def get_message_box_stylesheet(self):
        """Get stylesheet for message boxes"""
        return """
            QMessageBox {
                background-color: #202024;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #e4e4e7;
                font-size: 14px;
                background: transparent;
            }
            QMessageBox QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
                min-height: 36px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1d4ed8;
            }
            QMessageBox QPushButton:pressed {
                background-color: #1e40af;
            }
        """
    
    def apply_stylesheet(self):
        """Apply modern dark theme stylesheet"""
        self.setStyleSheet("""
            * {
                font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                border: none;
            }
            QMainWindow {
                background-color: #18181b;  /* Zinc 950 */
            }
            QWidget#leftPanel {
                background-color: #202024;  /* Zinc 900 */
                border-right: 1px solid #27272a;
            }
            QWidget#chatPanel {
                background-color: #18181b;  /* Zinc 950 */
            }
            
            /* List Widget Styling */
            QListWidget {
                background-color: transparent;
                border: none;
                padding: 8px;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                border-radius: 12px;
                padding: 2px;
                margin-bottom: 4px;
                color: #e4e4e7;  /* Zinc 200 */
                border: 1px solid transparent;
            }
            QListWidget::item:hover {
                background-color: #27272a;  /* Zinc 800 */
            }
            QListWidget::item:selected {
                background-color: #2563eb;  /* Blue 600 */
                color: #ffffff;
                border: 1px solid #3b82f6;
            }
            
            /* Chat List Specifics */
            QListWidget#chatList {
                background-color: #18181b;
                padding: 16px;
            }
            QListWidget#chatList::item {
                background-color: transparent;
                border: none;
                padding: 4px 0px;
            }
            QListWidget#chatList::item:hover {
                background-color: transparent;
            }
            QListWidget#chatList::item:selected {
                background-color: transparent;
            }

            /* Chat Area */
            QTextEdit {
                background-color: #18181b;
                border: none;
                padding: 20px;
                color: #e4e4e7;
            }
            
            /* Input Area */
            QLineEdit {
                background-color: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 24px;
                padding: 12px 20px;
                font-size: 14px;
                color: #ffffff;
                selection-background-color: #3b82f6;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #27272a;
            }
            
            /* Buttons */
            QPushButton {
                background-color: transparent;
                border-radius: 8px;
                padding: 8px;
                color: #e4e4e7;
            }
            QPushButton:hover {
                background-color: #3f3f46;
            }
            
            /* Primary Action Buttons (Add, Create) */
            QPushButton#addButton {
                background-color: #2563eb;  /* Blue 600 */
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton#addButton:hover {
                background-color: #1d4ed8;
            }
            
            /* Secondary Action Buttons (Edit) */
            QPushButton#editButton {
                background-color: #3f3f46;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton#editButton:hover {
                background-color: #52525b;
            }
            
            /* Destructive Action Buttons (Delete, Leave) */
            QPushButton#deleteButton {
                background-color: #ef4444;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton#deleteButton:hover {
                background-color: #dc2626;
            }
            
            /* Send Button */
            QPushButton#sendButton {
                background-color: #2563eb;
                color: white;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton#sendButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#sendButton:disabled {
                background-color: #27272a;
                color: #71717a;
            }
            
            /* Headers */
            QLabel#header, QLabel#chatHeader {
                background-color: #202024;
                color: #ffffff;
                padding: 16px 24px;
                font-size: 16px;
                font-weight: 600;
                border-bottom: 1px solid #27272a;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3f3f46;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Tab Widget - Box Style */
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background-color: #27272a;
                color: #a1a1aa;
                padding: 8px 16px;
                margin-right: 8px;
                border-radius: 6px;
                font-weight: 600;
                border: 1px solid transparent;
            }
            QTabBar::tab:selected {
                background-color: #3f3f46;
                color: #ffffff;
                border: 1px solid #52525b;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3f3f46;
                color: #e4e4e7;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #27272a;
                width: 1px;
            }
        """)
    
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
        """Create the left panel with tabs for contacts and groups"""
        from PyQt5.QtWidgets import QTabWidget
        
        panel = QWidget()
        panel.setObjectName("leftPanel")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Contacts tab
        contacts_tab = QWidget()
        contacts_layout = QVBoxLayout()
        contacts_layout.setContentsMargins(8, 12, 8, 8)
        contacts_layout.setSpacing(10)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.itemClicked.connect(self.on_contact_selected)
        contacts_layout.addWidget(self.contacts_list)
        
        # Contact management buttons
        contact_buttons_layout = QHBoxLayout()
        contact_buttons_layout.setSpacing(8)
        
        add_contact_btn = QPushButton("+ Add")
        add_contact_btn.setObjectName("addButton")
        add_contact_btn.clicked.connect(self.on_add_contact)
        contact_buttons_layout.addWidget(add_contact_btn)
        
        self.edit_contact_btn = QPushButton("✎ Edit")
        self.edit_contact_btn.setObjectName("editButton")
        self.edit_contact_btn.setEnabled(False)
        self.edit_contact_btn.clicked.connect(self.on_edit_contact)
        contact_buttons_layout.addWidget(self.edit_contact_btn)
        
        self.delete_contact_btn = QPushButton("✕ Delete")
        self.delete_contact_btn.setObjectName("deleteButton")
        self.delete_contact_btn.setEnabled(False)
        self.delete_contact_btn.clicked.connect(self.on_delete_contact)
        contact_buttons_layout.addWidget(self.delete_contact_btn)
        
        contacts_layout.addLayout(contact_buttons_layout)
        contacts_tab.setLayout(contacts_layout)
        
        # Groups tab
        groups_tab = QWidget()
        groups_layout = QVBoxLayout()
        groups_layout.setContentsMargins(8, 12, 8, 8)
        groups_layout.setSpacing(10)
        
        # Groups list
        self.groups_list = QListWidget()
        self.groups_list.itemClicked.connect(self.on_group_selected)
        groups_layout.addWidget(self.groups_list)
        
        # Group management buttons
        group_buttons_layout = QHBoxLayout()
        group_buttons_layout.setSpacing(8)
        
        create_group_btn = QPushButton("+ Create Space")
        create_group_btn.setObjectName("addButton")
        create_group_btn.clicked.connect(self.on_create_group)
        group_buttons_layout.addWidget(create_group_btn)
        
        self.leave_group_btn = QPushButton("✕ Leave Space")
        self.leave_group_btn.setObjectName("deleteButton")
        self.leave_group_btn.setEnabled(False)
        self.leave_group_btn.clicked.connect(self.on_leave_group)
        group_buttons_layout.addWidget(self.leave_group_btn)
        
        groups_layout.addLayout(group_buttons_layout)
        groups_tab.setLayout(groups_layout)
        
        # Add tabs
        self.tab_widget.addTab(contacts_tab, "Contacts")
        self.tab_widget.addTab(groups_tab, "Spaces")
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        panel.setLayout(layout)
        return panel
    
    def create_chat_panel(self):
        """Create the right chat panel"""
        panel = QWidget()
        panel.setObjectName("chatPanel")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat header
        self.chat_header = QLabel("Select a contact to start chatting")
        self.chat_header.setObjectName("chatHeader")
        self.chat_header.setMinimumHeight(60)
        layout.addWidget(self.chat_header)
        
        # Chat display area
        self.chat_display = QListWidget()
        self.chat_display.setObjectName("chatList")
        self.chat_display.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.chat_display.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.chat_display)
        
        # Message input area
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background-color: #202024;
                border-top: 1px solid #27272a;
                padding: 16px;
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)
        
        # Attachment button
        attach_btn = QPushButton("+")
        attach_btn.setObjectName("attachButton")
        attach_btn.setToolTip("Attach File")
        attach_btn.setEnabled(False)
        attach_btn.clicked.connect(self.on_attach_file)
        attach_btn.setStyleSheet("""
            QPushButton#attachButton {
                background-color: #3f3f46;
                color: #ffffff; 
                font-size: 20px;
                font-weight: bold;
                border-radius: 20px;
                padding: 0px;
                width: 40px;
                height: 40px;
            }
            QPushButton#attachButton:hover {
                background-color: #52525b;
            }
            QPushButton#attachButton:disabled {
                background-color: #27272a;
                color: #71717a;
            }
        """)
        self.attach_btn = attach_btn # Save reference
        input_layout.addWidget(attach_btn)
        
        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self.on_send_message)
        self.message_input.setEnabled(False)
        self.message_input.setMinimumHeight(44)
        input_layout.addWidget(self.message_input)
        
        # Emoji button
        emoji_btn = QPushButton("😊")
        emoji_btn.setObjectName("iconButton")
        emoji_btn.setToolTip("Add Emoji")
        emoji_btn.setEnabled(False)
        emoji_btn.setStyleSheet("color: #a1a1aa; font-size: 20px;")
        input_layout.addWidget(emoji_btn)
        
        # Send button
        self.send_btn = QPushButton("➤")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.clicked.connect(self.on_send_message)
        self.send_btn.setEnabled(False)
        self.send_btn.setToolTip("Send (Enter)")
        self.send_btn.setFixedSize(44, 44)
        input_layout.addWidget(self.send_btn)
        
        layout.addWidget(input_container)
        
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
        self.profile_map.clear()
        for profile in profiles:
            self.profile_map[profile.username] = profile
            
        # Rebuild the list with custom widgets
        for username in sorted(self.profile_map.keys()):
            self._add_contact_widget(username)

    def _add_contact_widget(self, username):
        """Helper to add a contact widget to the list"""
        item = QListWidgetItem()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Avatar circle with initials
        avatar_label = QLabel()
        initials = self.get_initials(username)
        avatar_color = self.get_avatar_color(username)
        avatar_label.setFixedSize(40, 40)
        avatar_label.setStyleSheet(f"""
            background-color: {avatar_color};
            color: white;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
        """)
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setText(initials)
        layout.addWidget(avatar_label)
        
        # Info container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Username
        name_label = QLabel(username)
        name_label.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600;")
        info_layout.addWidget(name_label)
        
        # Status/Last message placeholder
        status_label = QLabel("Click to chat")
        status_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        info_layout.addWidget(status_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        widget.setProperty("username", username)
        
        # Set explicit size to prevent clipping
        item.setSizeHint(QSize(0, 60))
        
        self.contacts_list.addItem(item)
        self.contacts_list.setItemWidget(item, widget)
    
    def add_contact_to_list(self, profile: PeerProfile):
        """Add a single contact to the list with avatar"""
        self.profile_map[profile.username] = profile
        
        # Rebuild the entire list to maintain sorting
        self.contacts_list.clear()
        for username in sorted(self.profile_map.keys()):
            self._add_contact_widget(username)
    
    def on_contact_selected(self, item):
        """Handle contact selection"""
        widget = self.contacts_list.itemWidget(item)
        if widget:
            username = widget.property("username")
        else:
            username = item.text()
        
        if not username:
            return
        
        self.current_peer = username
        self.current_group = None
        self.view_mode = "contact"
        self.chat_header.setText(f"🔒 {username}")
        self.send_btn.setEnabled(True)
        self.message_input.setEnabled(True)
        self.attach_btn.setEnabled(True)
        self.message_input.setFocus()
        self.edit_contact_btn.setEnabled(True)
        self.delete_contact_btn.setEnabled(True)
        
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
        """Handle send message for both P2P and group chats"""
        text = self.message_input.text().strip()
        if not text:
            return
        
        if self.view_mode == "group" and self.current_group:
            # Send group message
            self.send_group_message_signal.emit(self.current_group, text)
        elif self.view_mode == "contact" and self.current_peer:
            # Send P2P message
            self.send_message_signal.emit(self.current_peer, text)
        else:
            return
        
        # Clear input
        self.message_input.clear()
    
    def add_message_to_display(self, sender: str, text: str, timestamp: float, is_own: bool = False, status: str = "delivered"):
        """Add a message to the chat display with delivery status indicator"""
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
        
        # Status indicator (only for own messages)
        status_text = ""
        if is_own:
            if status == "delivered":
                status_text = " ✓✓"
            elif status == "queued":
                status_text = " ⏳"
            elif status == "failed":
                status_text = " !"
        
        # Create item and widget
        item = QListWidgetItem()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        
        # Bubble Container
        bubble_container = QWidget()
        bubble_layout = QVBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(12, 12, 12, 12)
        bubble_layout.setSpacing(4)
        
        # Check if it is a file transfer message
        if text.startswith("[FILE]"):
            try:
                file_data = json.loads(text[6:])
                filename = file_data.get('filename', 'Unknown File')
                size_bytes = file_data.get('size', 0)
                size_str = f"{size_bytes / 1024 / 1024:.2f} MB"
                
                # File Icon
                file_icon = QLabel("📄")
                file_icon.setStyleSheet("font-size: 24px; background: transparent; border: none;")
                
                # File Info
                info_layout = QVBoxLayout()
                name_label = QLabel(filename)
                name_label.setStyleSheet("font-weight: bold; color: #ffffff; border: none; background: transparent;")
                size_label = QLabel(size_str)
                size_label.setStyleSheet("color: #a1a1aa; font-size: 11px; border: none; background: transparent;")
                info_layout.addWidget(name_label)
                info_layout.addWidget(size_label)
                
                file_content_layout = QHBoxLayout()
                file_content_layout.addWidget(file_icon)
                file_content_layout.addLayout(info_layout)
                file_content_layout.addStretch()
                
                bubble_layout.addLayout(file_content_layout)
                
                # Download Button (only for received messages)
                if not is_own:
                    download_btn = QPushButton("Download")
                    download_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2563eb;
                            color: white;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-weight: 600;
                            border: none;
                        }
                        QPushButton:hover {
                            background-color: #1d4ed8;
                        }
                    """)
                    # Use lambda with default arg to capture current value
                    download_btn.clicked.connect(lambda checked=False, data=file_data, s=sender: self.on_download_file(data, s))
                    bubble_layout.addWidget(download_btn)
                else:
                    sent_label = QLabel("Sent via BitTorrent")
                    sent_label.setStyleSheet("color: #a1a1aa; font-style: italic; font-size: 11px; border: none; background: transparent;")
                    bubble_layout.addWidget(sent_label)
                    
            except json.JSONDecodeError:
                text_label = QLabel("Error: Invalid file message")
                text_label.setStyleSheet("color: #ef4444; border: none;")
                bubble_layout.addWidget(text_label)
        else:
            # Normal Text Message
            text_label = QLabel(text)
            text_label.setWordWrap(True)
            text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            # Important: Set max width on label so word wrap calculates height correctly
            text_label.setMaximumWidth(426) # 450 - 24 (padding)
            
            if is_own:
                text_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 400; border: none; padding: 0; margin: 0; background: transparent;")
            else:
                text_label.setStyleSheet("color: #e4e4e7; font-size: 14px; font-weight: 400; border: none; padding: 0; margin: 0; background: transparent;")
                
            bubble_layout.addWidget(text_label)
        
        # Metadata Label (Time + Status)
        meta_label = QLabel(f"{time_str}{status_text}")
        meta_label.setAlignment(Qt.AlignRight)
        
        if is_own:
            layout.addStretch()
            
            # Use ID selector to prevent style inheritance
            bubble_container.setObjectName("ownBubble")
            bubble_container.setStyleSheet("""
                #ownBubble {
                    background-color: rgba(255, 255, 255, 0.15);
                    border-radius: 18px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
            """)
            
            meta_label.setStyleSheet("color: #dbeafe; font-size: 11px; border: none; padding: 0; margin: 0; background: transparent;")
            
            bubble_layout.addWidget(meta_label)
            
            bubble_container.setMaximumWidth(450)
            layout.addWidget(bubble_container)
            
        else:
            # Avatar
            avatar_label = QLabel()
            initials = self.get_initials(sender)
            avatar_color = self.get_avatar_color(sender)
            avatar_label.setFixedSize(36, 36)
            avatar_label.setStyleSheet(f"""
                background-color: {avatar_color};
                color: white;
                border-radius: 18px;
                font-weight: 600;
                font-size: 13px;
            """)
            avatar_label.setAlignment(Qt.AlignCenter)
            avatar_label.setText(initials)
            
            # Align avatar to bottom of message
            avatar_container = QVBoxLayout()
            avatar_container.addStretch()
            avatar_container.addWidget(avatar_label)
            layout.addLayout(avatar_container)
            
            # Use ID selector
            bubble_container.setObjectName("peerBubble")
            bubble_container.setStyleSheet("""
                #peerBubble {
                    background-color: rgba(255, 255, 255, 0.08);
                    border-radius: 18px;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                }
            """)
            
            # Sender Name
            sender_label = QLabel(sender)
            sender_label.setStyleSheet(f"color: {avatar_color}; font-size: 12px; font-weight: bold; margin-bottom: 2px; border: none; padding: 0; background: transparent;")
            # Insert sender label at top
            bubble_layout.insertWidget(0, sender_label)
            
            meta_label.setStyleSheet("color: #a1a1aa; font-size: 11px; border: none; padding: 0; margin: 0; background: transparent;")
            
            bubble_layout.addWidget(meta_label)
            
            bubble_container.setMaximumWidth(450)
            layout.addWidget(bubble_container)
            layout.addStretch()
            
        # Add to list
        self.chat_display.addItem(item)
        self.chat_display.setItemWidget(item, widget)
        
        # Force layout update and adjust size hint with buffer
        widget.adjustSize()
        size = widget.sizeHint()
        item.setSizeHint(QSize(size.width(), size.height() + 10))
        
        self.chat_display.scrollToBottom()

    def on_download_file(self, file_data, sender):
        """Handle file download request"""
        filename = file_data.get('filename', 'downloaded_file')
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", filename)
        
        if save_path:
            peer_ip = "127.0.0.1" # Default fallback
            peer_port = file_data.get('seeder_port', 6882)
            
            # Try to resolve sender IP
            if sender in self.profile_map:
                peer_ip = self.profile_map[sender].host
            
            # Start download in a separate thread
            import threading
            threading.Thread(target=self._download_worker, args=(file_data, save_path, peer_ip, peer_port)).start()
            
            self.show_info("Download Started", f"Downloading {filename} from {sender}...")

    def _download_worker(self, file_data, save_path, peer_ip, peer_port):
        success = self.bt_manager.download_file(file_data, save_path, peer_ip, peer_port)
        # Note: In a real app, we should emit a signal to update UI with result
        print(f"Download {'completed' if success else 'failed'}: {save_path}")

    def load_conversation(self, username: str):
        """Load and display conversation history"""
        self.chat_display.clear()
        
        messages = self.conversations.get(username, [])
        for msg in messages:
            is_own = (msg.sender != username)
            status = getattr(msg, 'status', 'delivered')  # Get status, default to delivered
            self.add_message_to_display(msg.sender, msg.text, msg.timestamp, is_own, status)
    
    def add_message_to_conversation(self, username: str, message: Message, save_to_db: bool = True):
        """Add a message to conversation history"""
        if username not in self.conversations:
            self.conversations[username] = []
        
        self.conversations[username].append(message)
        
        # Update display if this is the current conversation
        if self.current_peer == username:
            is_own = (message.sender != username)
            status = getattr(message, 'status', 'delivered')  # Get status, default to delivered
            self.add_message_to_display(message.sender, message.text, message.timestamp, is_own, status)
    
    def on_edit_contact(self):
        """Handle edit contact button click"""
        if not self.current_peer:
            return
        
        profile = self.profile_map.get(self.current_peer)
        if not profile:
            self.show_error("Error", "Contact information not found")
            return
        
        from connect_dialog import ConnectDialog
        dialog = ConnectDialog(self, profile)
        if dialog.exec_():
            new_profile = dialog.get_profile()
            if new_profile:
                # Update profile map
                if new_profile.username != profile.username:
                    # Username changed - update everything
                    del self.profile_map[profile.username]
                    self.profile_map[new_profile.username] = new_profile
                    
                    # Update list
                    current_item = self.contacts_list.currentItem()
                    if current_item:
                        current_item.setText(new_profile.username)
                    
                    self.current_peer = new_profile.username
                    self.chat_header.setText(f"💬 Chat with {new_profile.username}")
                else:
                    self.profile_map[new_profile.username] = new_profile
                
                # Signal controller to save
                self.edit_contact_signal.emit(new_profile)
    
    def on_delete_contact(self):
        """Handle delete contact button click"""
        if not self.current_peer:
            return
        
        msg = QMessageBox(self)
        msg.setStyleSheet(self.get_message_box_stylesheet())
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Delete Contact")
        msg.setText(f"Are you sure you want to delete {self.current_peer}?")
        msg.setInformativeText("This will also delete all chat history with this contact.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        reply = msg.exec_()
        
        if reply == QMessageBox.Yes:
            # Remove from UI
            current_item = self.contacts_list.currentItem()
            if current_item:
                self.contacts_list.takeItem(self.contacts_list.row(current_item))
            
            # Remove from profile map
            if self.current_peer in self.profile_map:
                del self.profile_map[self.current_peer]
            
            # Remove from conversations
            if self.current_peer in self.conversations:
                del self.conversations[self.current_peer]
            
            # Signal controller to delete
            self.delete_contact_signal.emit(self.current_peer)
            
            # Clear chat area
            self.current_peer = None
            self.chat_header.setText("Select a contact to start chatting")
            self.chat_display.clear()
            self.message_input.clear()
            self.message_input.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.attach_btn.setEnabled(False)
            self.edit_contact_btn.setEnabled(False)
            self.delete_contact_btn.setEnabled(False)
    
    def on_tab_changed(self, index):
        """Handle tab change between contacts and groups"""
        # Clear current selection when switching tabs
        self.current_peer = None
        self.current_group = None
        self.message_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.attach_btn.setEnabled(False)
        self.chat_header.setText("Select a contact or space to start chatting")
        self.chat_display.clear()
    
    def on_group_selected(self, item):
        """Handle group selection"""
        widget = self.groups_list.itemWidget(item)
        if widget:
            group_id = widget.property("group_id")
            group_name = widget.property("group_name")
        else:
            return
            
        if group_id in self.groups:
            group = self.groups[group_id]
            self.current_group = group_id
            self.current_peer = None
            self.view_mode = "group"
            
            # Update header with group info
            member_count = len(group.members)
            self.chat_header.setText(f"{group.name} • {member_count} members")
            
            # Enable input
            self.message_input.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.attach_btn.setEnabled(True)
            self.message_input.setFocus()
            
            # Enable leave button
            self.leave_group_btn.setEnabled(True)
            
            # Load group conversation
            self.load_group_conversation(group_id)
    
    def on_create_group(self):
        """Handle create group button click"""
        # Get list of connected contacts
        available_contacts = list(self.profile_map.values())
        
        if len(available_contacts) < 2:
            msg = QMessageBox(self)
            msg.setStyleSheet(self.get_message_box_stylesheet())
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Cannot Create Space")
            msg.setText("You need at least 2 contacts to create a space.")
            msg.setInformativeText("Add more contacts first!")
            msg.exec_()
            return
        
        dialog = GroupDialog(self, available_contacts)
        if dialog.exec_():
            group_data = dialog.get_group_data()
            if group_data:
                # Emit signal to create group
                self.create_group_signal.emit(group_data['name'], group_data['members'])
    
    def on_leave_group(self):
        """Handle leave group button click"""
        if not self.current_group:
            return
        
        group = self.groups.get(self.current_group)
        if not group:
            return
        
        msg = QMessageBox(self)
        msg.setStyleSheet(self.get_message_box_stylesheet())
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Delete Space")
        msg.setText(f"Are you sure you want to delete space '{group.name}'?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        reply = msg.exec_()
        
        if reply == QMessageBox.Yes:
            # TODO: Implement leave group functionality
            self.show_info("Leave Space", "Leave space functionality coming soon!")
    
    def add_group_to_list(self, group: Group):
        """Add a group to the groups list"""
        self.groups[group.group_id] = group
        
        # Update groups list widget
        self.groups_list.clear()
        for g in self.groups.values():
            item = QListWidgetItem()
            # Create widget with avatar and name
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(12)
            
            # Group avatar (using group icon)
            avatar_label = QLabel()
            avatar_label.setFixedSize(40, 40)
            avatar_label.setStyleSheet("""
                background-color: #2563eb;
                color: white;
                border-radius: 20px;
                font-weight: 600;
                font-size: 16px;
            """)
            avatar_label.setAlignment(Qt.AlignCenter)
            avatar_label.setText("👥")
            layout.addWidget(avatar_label)
            
            # Info container
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            info_layout.setContentsMargins(0, 0, 0, 0)
            
            # Group name
            name_label = QLabel(g.name)
            name_label.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600;")
            info_layout.addWidget(name_label)
            
            # Member count
            count_label = QLabel(f"{len(g.members)} members")
            count_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
            info_layout.addWidget(count_label)
            
            layout.addLayout(info_layout)
            layout.addStretch()
            
            widget.setProperty("group_id", g.group_id)  # Store for selection
            widget.setProperty("group_name", g.name)
            
            # Set explicit size to prevent clipping
            item.setSizeHint(QSize(0, 60))
            
            self.groups_list.addItem(item)
            self.groups_list.setItemWidget(item, widget)
    
    def load_group_conversation(self, group_id: str):
        """Load and display group conversation history"""
        self.chat_display.clear()
        
        messages = self.group_conversations.get(group_id, [])
        for msg in messages:
            status = getattr(msg, 'status', 'delivered')
            self.add_message_to_display(msg.from_user, msg.text, msg.timestamp, False, status)
    
    def add_group_message_to_conversation(self, group_id: str, message: GroupMessage):
        """Add a group message to conversation history"""
        if group_id not in self.group_conversations:
            self.group_conversations[group_id] = []
        
        self.group_conversations[group_id].append(message)
        
        # Update display if this is the current group conversation
        if self.current_group == group_id and self.view_mode == "group":
            status = getattr(message, 'status', 'delivered')
            self.add_message_to_display(message.from_user, message.text, message.timestamp, False, status)
    
    def on_attach_file(self):
        """Handle file attachment"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Send")
        if file_path:
            self.send_file_via_bittorrent(file_path)

    def send_file_via_bittorrent(self, file_path):
        """Initiate file transfer using BitTorrent protocol."""
        try:
            # Create torrent descriptor
            torrent_data = self.bt_manager.create_torrent(file_path)
            
            # Create message payload
            msg_text = "[FILE]" + json.dumps(torrent_data)
            
            if self.view_mode == "group" and self.current_group:
                self.send_group_message_signal.emit(self.current_group, msg_text)
            elif self.view_mode == "contact" and self.current_peer:
                self.send_message_signal.emit(self.current_peer, msg_text)
                
        except Exception as e:
            self.show_error("Error", f"Failed to send file: {str(e)}")

    def show_about(self):
        """Show about dialog"""
        msg = QMessageBox(self)
        msg.setStyleSheet(self.get_message_box_stylesheet())
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About P2P Chat")
        msg.setText(
            "<h3>P2P Chat Application 🔒</h3>"
            "<p>A peer-to-peer chat application built with Python and PyQt5.</p>"
            "<p>Connect with friends directly without a central server.</p>"
            "<p><b>🔐 End-to-End Encryption:</b> All messages encrypted with RSA-2048 + AES-256</p>"
            "<p><b>👥 Spaces:</b> Create spaces with mesh network architecture</p>"
            "<p><b>⏳ Offline Messaging:</b> Messages queued and delivered when online</p>"
            "<p>Your conversations are secure and private!</p>"
        )
        msg.exec_()
    
    def show_error(self, title: str, message: str):
        """Show an error message"""
        msg = QMessageBox(self)
        msg.setStyleSheet(self.get_message_box_stylesheet())
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
    
    def show_info(self, title: str, message: str):
        """Show an info message"""
        msg = QMessageBox(self)
        msg.setStyleSheet(self.get_message_box_stylesheet())
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
