"""Message and conversation data models"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Message:
    """Represents a single chat message"""
    sender: str
    receiver: str
    text: str
    timestamp: float
    status: str = "delivered"  # "delivered", "queued", "failed"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "text": self.text,
            "timestamp": self.timestamp,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            text=data["text"],
            timestamp=data["timestamp"],
            status=data.get("status", "delivered")
        )


@dataclass
class Conversation:
    """Represents a conversation with a peer"""
    peer_username: str
    messages: List[Message] = field(default_factory=list)
    
    def add_message(self, message: Message):
        """Add a message to this conversation"""
        self.messages.append(message)
    
    def get_recent_messages(self, limit: int = 50):
        """Get the most recent messages"""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages
