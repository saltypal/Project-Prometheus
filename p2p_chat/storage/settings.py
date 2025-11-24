"""Settings storage and retrieval"""

import json
import os
from pathlib import Path


def get_config_dir() -> Path:
    """Get the configuration directory path"""
    # Allow override via environment variable for testing
    env_config = os.getenv('P2P_CHAT_CONFIG')
    if env_config:
        config_dir = Path(env_config)
    else:
        config_dir = Path.home() / ".p2p_chat"
    
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_settings_file() -> Path:
    """Get the settings JSON file path"""
    return get_config_dir() / "settings.json"


def load_settings() -> dict:
    """Load settings from JSON file"""
    settings_file = get_settings_file()
    
    default_settings = {
        "username": "",
        "listen_port": 12345
    }
    
    if not settings_file.exists():
        return default_settings
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            return {**default_settings, **data}
    except (json.JSONDecodeError, FileNotFoundError):
        return default_settings


def save_settings(settings: dict):
    """Save settings to JSON file"""
    settings_file = get_settings_file()
    
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")
