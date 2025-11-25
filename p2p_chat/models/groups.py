"""Data models for group chats"""

from dataclasses import dataclass, field
from typing import List, Optional
import time


@dataclass
class Group:
    """Represents a group chat
    
    Attributes:
        group_id: Unique identifier for the group
        name: Display name of the group
        members: List of usernames in the group
        creator: Username of the group creator
        created_at: Unix timestamp when group was created
        group_key: Encrypted group AES key (base64)
    """
    group_id: str
    name: str
    members: List[str]
    creator: str
    created_at: float = field(default_factory=time.time)
    group_key: Optional[str] = None  # AES key encrypted with our RSA private key
    
    def __post_init__(self):
        """Ensure members list is always sorted for consistency"""
        self.members = sorted(set(self.members))  # Remove duplicates and sort
    
    def has_member(self, username: str) -> bool:
        """Check if a user is a member of this group"""
        return username in self.members
    
    def add_member(self, username: str):
        """Add a member to the group"""
        if username not in self.members:
            self.members.append(username)
            self.members.sort()
    
    def remove_member(self, username: str):
        """Remove a member from the group"""
        if username in self.members:
            self.members.remove(username)
    
    def get_other_members(self, my_username: str) -> List[str]:
        """Get all members except the specified user"""
        return [m for m in self.members if m != my_username]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'group_id': self.group_id,
            'name': self.name,
            'members': self.members,
            'creator': self.creator,
            'created_at': self.created_at,
            'group_key': self.group_key
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Group':
        """Create Group from dictionary"""
        return Group(
            group_id=data['group_id'],
            name=data['name'],
            members=data['members'],
            creator=data['creator'],
            created_at=data.get('created_at', time.time()),
            group_key=data.get('group_key')
        )


@dataclass
class GroupMessage:
    """Represents a message in a group chat
    
    Attributes:
        group_id: ID of the group this message belongs to
        from_user: Username of the sender
        text: Message content (plaintext after decryption)
        timestamp: Unix timestamp when message was sent
        msg_id: Unique message identifier (UUID)
        status: Delivery status ("delivered", "queued", "failed")
    """
    group_id: str
    from_user: str
    text: str
    timestamp: float = field(default_factory=time.time)
    msg_id: Optional[str] = None
    status: str = "delivered"  # "delivered", "queued", "failed"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'group_id': self.group_id,
            'from_user': self.from_user,
            'text': self.text,
            'timestamp': self.timestamp,
            'msg_id': self.msg_id,
            'status': self.status
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'GroupMessage':
        """Create GroupMessage from dictionary"""
        return GroupMessage(
            group_id=data['group_id'],
            from_user=data['from_user'],
            text=data['text'],
            timestamp=data.get('timestamp', time.time()),
            msg_id=data.get('msg_id'),
            status=data.get('status', 'delivered')
        )
