"""Main entry point for P2P Chat GUI application"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from storage import load_settings, save_settings
from main_window import MainWindow
from controller import ChatController


def get_username():
    """Get username from settings or prompt user"""
    settings = load_settings()
    username = settings.get("username", "")
    
    if not username:
        # Prompt for username on first run
        username, ok = QInputDialog.getText(
            None,
            "Welcome to P2P Chat",
            "Please enter your username:",
            text=""
        )
        
        if not ok or not username.strip():
            QMessageBox.critical(None, "Error", "Username is required to use P2P Chat")
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
    window.show_info(
        "Welcome",
        f"Welcome, {username}!\n\n"
        f"Listening on port {listen_port}.\n"
        f"Add contacts to start chatting."
    )
    
    # Run application
    exit_code = app.exec_()
    
    # Cleanup
    controller.shutdown()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
