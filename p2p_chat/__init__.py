"""
P2P Chat - Peer-to-Peer Chat Application

A simple peer-to-peer chat application with GUI support.

To run the GUI application:
    python -m p2p_chat.gui.main

To run the CLI demo:
    python -m p2p_chat.chat
"""

from .peer import Peer
from .connection import Connection

__version__ = "1.0.0"
__all__ = ["Peer", "Connection"]
