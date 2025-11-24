"""Main entry point for P2P Chat GUI application"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from storage import load_settings, save_settings
from main_window import MainWindow
from controller import ChatController


def get_dark_theme_stylesheet():
    """Get dark theme stylesheet for dialogs"""
    return """
        QDialog, QMessageBox, QInputDialog {
            background-color: #202024;
            color: #ffffff;
        }
        QDialog QLabel, QMessageBox QLabel, QInputDialog QLabel {
            color: #e4e4e7;
            font-size: 14px;
            background: transparent;
        }
        QDialog QPushButton, QMessageBox QPushButton, QInputDialog QPushButton {
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
        QDialog QPushButton:hover, QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {
            background-color: #1d4ed8;
        }
        QDialog QPushButton:pressed, QMessageBox QPushButton:pressed, QInputDialog QPushButton:pressed {
            background-color: #1e40af;
        }
        QLineEdit {
            background-color: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 14px;
            color: #ffffff;
            selection-background-color: #2563eb;
            selection-color: white;
            min-height: 36px;
        }
        QLineEdit:focus {
            border: 1px solid #2563eb;
            background-color: #27272a;
        }
    """


def get_username():
    """Get username from settings or prompt user"""
    settings = load_settings()
    username = settings.get("username", "")
    
    if not username:
        # Prompt for username on first run
        dialog = QInputDialog()
        dialog.setStyleSheet(get_dark_theme_stylesheet())
        dialog.setWindowTitle("Welcome to P2P Chat")
        dialog.setLabelText("Please enter your username:")
        dialog.setInputMode(QInputDialog.TextInput)
        ok = dialog.exec_()
        username = dialog.textValue()
        
        if not ok or not username.strip():
            msg = QMessageBox()
            msg.setStyleSheet(get_dark_theme_stylesheet())
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("Username is required to use P2P Chat")
            msg.exec_()
            sys.exit(1)
        
        username = username.strip()
        settings["username"] = username
        save_settings(settings)
    
    return username


def main():
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("P2P Chat")
    
    # Get username
    username = get_username()
    
    # Load settings
    settings = load_settings()
    listen_port = settings.get("listen_port", 12345)
    
    # Create main window
    window = MainWindow()
    
    # Create controller
    controller = ChatController(window, username, listen_port)
    
    # Load profiles
    controller.load_profiles()
    
    # Show window
    window.show()
    
    # Show welcome message
    msg = QMessageBox(window)
    msg.setStyleSheet(get_dark_theme_stylesheet())
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Welcome")
    msg.setText(f"Welcome, {username}!\n\nListening on port {listen_port}.\nAdd contacts to start chatting.")
    msg.exec_()
    
    # Run application
    exit_code = app.exec_()
    
    # Cleanup
    controller.shutdown()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
