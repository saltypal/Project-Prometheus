"""Profile storage and retrieval"""

import json
from pathlib import Path
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.peers import PeerProfile


def get_config_dir() -> Path:
    """Get the configuration directory path"""
    config_dir = Path.home() / ".p2p_chat"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_profiles_file() -> Path:
    """Get the profiles JSON file path"""
    return get_config_dir() / "profiles.json"


def load_profiles() -> List[PeerProfile]:
    """Load peer profiles from JSON file"""
    profiles_file = get_profiles_file()
    
    if not profiles_file.exists():
        return []
    
    try:
        with open(profiles_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [PeerProfile.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, FileNotFoundError):
        return []


def save_profiles(profiles: List[PeerProfile]):
    """Save peer profiles to JSON file"""
    profiles_file = get_profiles_file()
    
    try:
        data = [profile.to_dict() for profile in profiles]
        with open(profiles_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving profiles: {e}")
