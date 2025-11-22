"""Peer profile data model"""

from dataclasses import dataclass


@dataclass
class PeerProfile:
    """Represents a known peer contact"""
    username: str
    host: str
    port: int
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "username": self.username,
            "host": self.host,
            "port": self.port
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        return cls(
            username=data["username"],
            host=data["host"],
            port=data["port"]
        )
