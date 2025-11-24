"""Storage for group chat data"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from models.groups import Group
from storage.settings import get_config_dir


def get_groups_file() -> Path:
    """Get the groups JSON file path"""
    return get_config_dir() / "groups.json"


def load_groups() -> List[Group]:
    """Load all groups from storage
    
    Returns:
        List of Group objects
    """
    groups_file = get_groups_file()
    
    if not groups_file.exists():
        return []
    
    try:
        with open(groups_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [Group.from_dict(g) for g in data]
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"Error loading groups: {e}")
        return []


def save_groups(groups: List[Group]):
    """Save all groups to storage
    
    Args:
        groups: List of Group objects to save
    """
    groups_file = get_groups_file()
    
    try:
        with open(groups_file, 'w', encoding='utf-8') as f:
            data = [g.to_dict() for g in groups]
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving groups: {e}")


def add_group(group: Group):
    """Add a new group to storage
    
    Args:
        group: Group object to add
    """
    groups = load_groups()
    
    # Check if group already exists
    existing_ids = [g.group_id for g in groups]
    if group.group_id in existing_ids:
        # Update existing group
        groups = [g if g.group_id != group.group_id else group for g in groups]
    else:
        # Add new group
        groups.append(group)
    
    save_groups(groups)


def remove_group(group_id: str):
    """Remove a group from storage
    
    Args:
        group_id: ID of the group to remove
    """
    groups = load_groups()
    groups = [g for g in groups if g.group_id != group_id]
    save_groups(groups)


def get_group(group_id: str) -> Optional[Group]:
    """Get a specific group by ID
    
    Args:
        group_id: ID of the group to retrieve
        
    Returns:
        Group object if found, None otherwise
    """
    groups = load_groups()
    for group in groups:
        if group.group_id == group_id:
            return group
    return None


def update_group_key(group_id: str, encrypted_key: str):
    """Update the encrypted group key for a group
    
    Args:
        group_id: ID of the group
        encrypted_key: Base64-encoded encrypted AES key
    """
    groups = load_groups()
    
    for group in groups:
        if group.group_id == group_id:
            group.group_key = encrypted_key
            break
    
    save_groups(groups)


def get_user_groups(username: str) -> List[Group]:
    """Get all groups that a user is a member of
    
    Args:
        username: Username to search for
        
    Returns:
        List of Group objects the user is a member of
    """
    groups = load_groups()
    return [g for g in groups if g.has_member(username)]
