"""
End-to-End Encryption Module using Hybrid RSA + AES Cryptography

This module provides automatic encryption/decryption with zero user interaction.
- RSA-2048 for key exchange
- AES-256 in CBC mode for message encryption
- New AES key generated per message (forward secrecy)
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import os
import base64
import uuid
from typing import Dict, Optional


class E2EEncryption:
    """Handles end-to-end encryption with hybrid RSA + AES"""
    
    def __init__(self):
        """Initialize encryption - generates RSA key pair"""
        # Generate RSA key pair on startup (2048-bit for security)
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
        # Store peer public keys: username -> public_key
        self.peer_public_keys: Dict[str, rsa.RSAPublicKey] = {}
        
        # Store group keys: group_id -> AES key (32 bytes)
        self.group_keys: Dict[str, bytes] = {}
        
        print("🔐 E2E Encryption initialized - RSA key pair generated")
    
    def get_public_key_pem(self) -> str:
        """
        Export public key as PEM string to send to peers.
        
        Returns:
            Base64 encoded PEM string of public key
        """
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(pem).decode('utf-8')
    
    def add_peer_public_key(self, username: str, public_key_pem: str):
        """
        Store peer's public key for future encryption.
        
        Args:
            username: Peer's username
            public_key_pem: Base64 encoded PEM string of peer's public key
        """
        try:
            pem_bytes = base64.b64decode(public_key_pem.encode('utf-8'))
            public_key = serialization.load_pem_public_key(
                pem_bytes,
                backend=default_backend()
            )
            self.peer_public_keys[username] = public_key
            print(f"🔑 Stored public key for {username}")
        except Exception as e:
            print(f"❌ Error storing public key for {username}: {e}")
            raise
    
    def has_peer_key(self, username: str) -> bool:
        """Check if we have a peer's public key"""
        return username in self.peer_public_keys
    
    def encrypt_message(self, username: str, plaintext: str) -> Dict[str, str]:
        """
        Encrypt a message for a specific peer using hybrid encryption.
        
        Process:
        1. Generate random AES-256 key
        2. Encrypt message with AES
        3. Encrypt AES key with peer's RSA public key
        4. Return encrypted data
        
        Args:
            username: Recipient's username
            plaintext: Message to encrypt
            
        Returns:
            Dictionary with encrypted_message, encrypted_key, and iv (all base64)
            
        Raises:
            ValueError: If peer's public key not found
        """
        if username not in self.peer_public_keys:
            raise ValueError(f"No public key for {username} - cannot encrypt")
        
        try:
            # 1. Generate random AES key (32 bytes = 256 bits)
            aes_key = os.urandom(32)
            iv = os.urandom(16)  # AES block size
            
            # 2. Encrypt message with AES-256-CBC
            cipher = Cipher(
                algorithms.AES(aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad plaintext to AES block size (16 bytes) using PKCS7
            plaintext_bytes = plaintext.encode('utf-8')
            padding_length = 16 - (len(plaintext_bytes) % 16)
            padded_plaintext = plaintext_bytes + bytes([padding_length] * padding_length)
            
            # Encrypt the message
            encrypted_message = encryptor.update(padded_plaintext) + encryptor.finalize()
            
            # 3. Encrypt AES key with peer's RSA public key
            peer_public_key = self.peer_public_keys[username]
            encrypted_key = peer_public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # 4. Return base64 encoded data
            return {
                'encrypted_message': base64.b64encode(encrypted_message).decode('utf-8'),
                'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8')
            }
            
        except Exception as e:
            print(f"❌ Encryption error for {username}: {e}")
            raise
    
    def decrypt_message(self, encrypted_data: Dict[str, str]) -> str:
        """
        Decrypt a received message using hybrid decryption.
        
        Process:
        1. Decrypt AES key using our RSA private key
        2. Decrypt message using AES key
        3. Remove padding and return plaintext
        
        Args:
            encrypted_data: Dictionary with encrypted_message, encrypted_key, iv
            
        Returns:
            Decrypted plaintext message
            
        Raises:
            ValueError: If decryption fails
        """
        try:
            # 1. Decode base64
            encrypted_message = base64.b64decode(encrypted_data['encrypted_message'])
            encrypted_key = base64.b64decode(encrypted_data['encrypted_key'])
            iv = base64.b64decode(encrypted_data['iv'])
            
            # 2. Decrypt AES key with our RSA private key
            aes_key = self.private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # 3. Decrypt message with AES key
            cipher = Cipher(
                algorithms.AES(aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(encrypted_message) + decryptor.finalize()
            
            # 4. Remove PKCS7 padding
            padding_length = padded_plaintext[-1]
            plaintext = padded_plaintext[:-padding_length]
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            raise ValueError(f"Failed to decrypt message: {e}")
    
    def remove_peer_key(self, username: str):
        """Remove a peer's public key (e.g., when they disconnect)"""
        if username in self.peer_public_keys:
            del self.peer_public_keys[username]
            print(f"🔓 Removed public key for {username}")
    
    # ==================== GROUP CHAT ENCRYPTION ====================
    
    def create_group_key(self, group_id: str) -> bytes:
        """
        Generate a new AES-256 key for a group.
        
        Args:
            group_id: Unique identifier for the group
            
        Returns:
            32-byte AES key (stored internally)
        """
        # Generate random 256-bit (32 byte) AES key
        group_key = os.urandom(32)
        self.group_keys[group_id] = group_key
        print(f"🔑 Generated group key for {group_id}")
        return group_key
    
    def add_group_key(self, group_id: str, group_key: bytes):
        """
        Add an existing group key (received from group creator).
        
        Args:
            group_id: Group identifier
            group_key: 32-byte AES key
        """
        self.group_keys[group_id] = group_key
        print(f"🔑 Added group key for {group_id}")
    
    def encrypt_group_key_for_member(self, group_key: bytes, member_username: str) -> str:
        """
        Encrypt a group key with a member's RSA public key.
        
        Args:
            group_key: The 32-byte AES group key to encrypt
            member_username: Username of the member
            
        Returns:
            Base64-encoded encrypted key
            
        Raises:
            ValueError: If member's public key not found
        """
        if member_username not in self.peer_public_keys:
            raise ValueError(f"No public key for {member_username}")
        
        # Encrypt the group key with member's RSA public key
        member_public_key = self.peer_public_keys[member_username]
        encrypted_key = member_public_key.encrypt(
            group_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted_key).decode('utf-8')
    
    def decrypt_group_key(self, encrypted_key_b64: str) -> bytes:
        """
        Decrypt a group key that was encrypted with our RSA public key.
        
        Args:
            encrypted_key_b64: Base64-encoded encrypted group key
            
        Returns:
            Decrypted 32-byte AES group key
        """
        encrypted_key = base64.b64decode(encrypted_key_b64)
        
        # Decrypt with our private key
        group_key = self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return group_key
    
    def encrypt_group_message(self, group_id: str, plaintext: str) -> Dict[str, str]:
        """
        Encrypt a message for a group using the shared group key.
        
        Args:
            group_id: ID of the group
            plaintext: Message to encrypt
            
        Returns:
            Dictionary with encrypted_message and iv (both base64)
            
        Raises:
            ValueError: If group key not found
        """
        if group_id not in self.group_keys:
            raise ValueError(f"No key for group {group_id}")
        
        try:
            group_key = self.group_keys[group_id]
            iv = os.urandom(16)  # Random IV for each message
            
            # Encrypt with AES-256-CBC
            cipher = Cipher(
                algorithms.AES(group_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad plaintext to AES block size (16 bytes) using PKCS7
            padded_plaintext = self._pad(plaintext.encode('utf-8'))
            ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
            
            return {
                'encrypted_message': base64.b64encode(ciphertext).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8')
            }
            
        except Exception as e:
            print(f"❌ Group encryption error: {e}")
            raise
    
    def decrypt_group_message(self, group_id: str, encrypted_data: Dict[str, str]) -> str:
        """
        Decrypt a group message using the shared group key.
        
        Args:
            group_id: ID of the group
            encrypted_data: Dictionary with 'encrypted_message' and 'iv' (base64)
            
        Returns:
            Decrypted plaintext message
            
        Raises:
            ValueError: If group key not found or decryption fails
        """
        if group_id not in self.group_keys:
            raise ValueError(f"No key for group {group_id}")
        
        try:
            group_key = self.group_keys[group_id]
            ciphertext = base64.b64decode(encrypted_data['encrypted_message'])
            iv = base64.b64decode(encrypted_data['iv'])
            
            # Decrypt with AES-256-CBC
            cipher = Cipher(
                algorithms.AES(group_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            plaintext = self._unpad(padded_plaintext).decode('utf-8')
            
            return plaintext
            
        except Exception as e:
            print(f"❌ Group decryption error: {e}")
            raise ValueError(f"Failed to decrypt group message: {e}")
