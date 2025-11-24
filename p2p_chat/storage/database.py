"""
Database module for persistent chat history storage using SQLite.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import sys

# Handle imports for both module and direct execution
try:
    from models.messages import Message
    from models.groups import GroupMessage
except ImportError:
    from ..models.messages import Message
    from ..models.groups import GroupMessage


def get_db_path() -> Path:
    """Get the path to the SQLite database file."""
    config_dir = Path.home() / '.p2p_chat'
    config_dir.mkdir(exist_ok=True)
    return config_dir / 'chat_history.db'


class ChatDatabase:
    """Manages SQLite database for chat message history."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the database file (uses default if None)
        """
        self.db_path = db_path or get_db_path()
        self._init_database()
    
    def _init_database(self):
        """Create the messages and group_messages tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # P2P messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp REAL NOT NULL,
                is_outgoing INTEGER NOT NULL DEFAULT 0
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_participants 
            ON messages(sender, receiver)
        ''')
        
        # Group messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                from_user TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp REAL NOT NULL,
                msg_id TEXT UNIQUE
            )
        ''')
        
        # Create index for faster group message queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_group 
            ON group_messages(group_id, timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_message(self, message: Message, is_outgoing: bool = False):
        """
        Save a message to the database.
        
        Args:
            message: Message object to save
            is_outgoing: True if this is a sent message, False if received
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (sender, receiver, text, timestamp, is_outgoing)
            VALUES (?, ?, ?, ?, ?)
        ''', (message.sender, message.receiver, message.text, 
              message.timestamp, 1 if is_outgoing else 0))
        
        conn.commit()
        conn.close()
    
    def get_conversation(self, username1: str, username2: str, limit: int = 100) -> List[Message]:
        """
        Retrieve conversation history between two users.
        
        Args:
            username1: First participant username
            username2: Second participant username
            limit: Maximum number of messages to retrieve (most recent)
        
        Returns:
            List of Message objects sorted by timestamp (oldest to newest)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sender, receiver, text, timestamp
            FROM messages
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (username1, username2, username2, username1, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to Message objects and reverse (oldest first)
        messages = [Message(sender=row[0], receiver=row[1], 
                           text=row[2], timestamp=row[3]) 
                   for row in reversed(rows)]
        
        return messages
    
    def get_recent_conversations(self, username: str, limit: int = 50) -> List[str]:
        """
        Get list of usernames with recent conversations.
        
        Args:
            username: Current user's username
            limit: Maximum number of conversation partners to return
        
        Returns:
            List of usernames sorted by most recent message
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT
                CASE 
                    WHEN sender = ? THEN receiver
                    ELSE sender
                END as peer_username,
                MAX(timestamp) as last_message_time
            FROM messages
            WHERE sender = ? OR receiver = ?
            GROUP BY peer_username
            ORDER BY last_message_time DESC
            LIMIT ?
        ''', (username, username, username, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def delete_conversation(self, username1: str, username2: str):
        """
        Delete all messages in a conversation.
        
        Args:
            username1: First participant username
            username2: Second participant username
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM messages
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ''', (username1, username2, username2, username1))
        
        conn.commit()
        conn.close()
    
    def search_messages(self, query: str, username: Optional[str] = None) -> List[Message]:
        """
        Search for messages containing specific text.
        
        Args:
            query: Text to search for
            username: Optional - limit search to conversations with this user
        
        Returns:
            List of matching Message objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if username:
            cursor.execute('''
                SELECT sender, receiver, text, timestamp
                FROM messages
                WHERE text LIKE ? AND (sender = ? OR receiver = ?)
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (f'%{query}%', username, username))
        else:
            cursor.execute('''
                SELECT sender, receiver, text, timestamp
                FROM messages
                WHERE text LIKE ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (f'%{query}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = [Message(sender=row[0], receiver=row[1], 
                           text=row[2], timestamp=row[3]) 
                   for row in rows]
        
        return messages
    
    def get_message_count(self, username1: str, username2: str) -> int:
        """
        Get the total number of messages in a conversation.
        
        Args:
            username1: First participant username
            username2: Second participant username
        
        Returns:
            Total message count
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*)
            FROM messages
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ''', (username1, username2, username2, username1))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def close(self):
        """Close database connections (SQLite auto-closes, but kept for API consistency)."""
        pass
    
    # ==================== GROUP CHAT DATABASE METHODS ====================
    
    def save_group_message(self, message: GroupMessage):
        """
        Save a group message to the database.
        
        Args:
            message: GroupMessage object to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO group_messages (group_id, from_user, text, timestamp, msg_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (message.group_id, message.from_user, message.text, 
                  message.timestamp, message.msg_id))
            
            conn.commit()
        except sqlite3.IntegrityError:
            # Duplicate msg_id (message already received)
            print(f"⚠️ Duplicate message {message.msg_id} - already in database")
        finally:
            conn.close()
    
    def get_group_conversation(self, group_id: str, limit: int = 100) -> List[GroupMessage]:
        """
        Get messages for a group chat.
        
        Args:
            group_id: Group identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of GroupMessage objects, ordered by timestamp
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT group_id, from_user, text, timestamp, msg_id
            FROM group_messages
            WHERE group_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (group_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = [GroupMessage(
            group_id=row[0],
            from_user=row[1],
            text=row[2],
            timestamp=row[3],
            msg_id=row[4]
        ) for row in rows]
        
        return messages
    
    def get_group_message_count(self, group_id: str) -> int:
        """
        Get the total number of messages in a group.
        
        Args:
            group_id: Group identifier
            
        Returns:
            Total message count
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*)
            FROM group_messages
            WHERE group_id = ?
        ''', (group_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def delete_group_messages(self, group_id: str):
        """
        Delete all messages for a group.
        
        Args:
            group_id: Group identifier
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM group_messages
            WHERE group_id = ?
        ''', (group_id,))
        
        conn.commit()
        conn.close()
