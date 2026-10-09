"""
storage.py — reading and writing the vault file on disk.

A vault file looks like this, all concatenated:

    [ magic ][ version ][ salt ][ nonce+ciphertext ]
      4 bytes   1 byte    16 B      variable

The magic bytes are a fixed fingerprint so we can tell "this is a Janus
Lock file" from "this is a random file the user pointed at."
The version byte lets us change the format later without breaking old vaults.
"""

import os
from pathlib import Path

from januslock import crypto

MAGIC = b"JNUS"          # 4 bytes — our file fingerprint
VERSION = 1              # bump this if the format ever changes

VAULT_SUFFIX = ".janus"  # so we can spot our files by name too


def _build_file_bytes(salt: bytes, encrypted_blob: bytes) -> bytes:
    """Assemble the on-disk format from its pieces."""
    return MAGIC + bytes([VERSION]) + salt + encrypted_blob


def _parse_file_bytes(data: bytes) -> tuple[bytes, bytes]:
    """
    Split a vault file back into (salt, encrypted_blob).
    Raises ValueError if this isn't a Janus Lock file.
    """
    if len(data) < len(MAGIC) + 1 + crypto.SALT_SIZE:
        raise ValueError("File too small to be a Janus Lock vault.")

    if data[:len(MAGIC)] != MAGIC:
        raise ValueError("Not a Janus Lock vault (bad magic bytes).")

    version = data[len(MAGIC)]
    if version != VERSION:
        raise ValueError(f"Unsupported vault version: {version}")

    offset = len(MAGIC) + 1
    salt = data[offset:offset + crypto.SALT_SIZE]
    encrypted_blob = data[offset + crypto.SALT_SIZE:]
    return salt, encrypted_blob


def save_vault(path: Path, plaintext: bytes, key: bytes, salt: bytes) -> None:
    """
    Encrypt plaintext and write a vault file ATOMICALLY.

    'Atomic' means: write to a temp file, then rename over the target.
    Rename is atomic on the OS level, so a crash leaves you with either
    the OLD vault or the NEW vault — never a half-written corrupt one.
    """
    encrypted = crypto.encrypt(plaintext, key)
    file_bytes = _build_file_bytes(salt, encrypted)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(file_bytes)
    os.replace(tmp_path, path)      # atomic swap


def load_vault(path: Path, password: str) -> tuple[bytes, bytes, bytes]:
    """
    Read a vault file and decrypt it.

    Returns (plaintext, key, salt). We hand the key and salt back to the
    caller because the UI will need them later to save again.
    Raises ValueError for format problems, and cryptography's InvalidTag
    for a wrong password.
    """
    data = path.read_bytes()
    salt, encrypted_blob = _parse_file_bytes(data)

    key = crypto.derive_key(password, salt)
    plaintext = crypto.decrypt(encrypted_blob, key)

    return plaintext, key, salt


def create_vault(path: Path, password: str) -> tuple[bytes, bytes]:
    """
    Create a brand-new EMPTY vault.
    Generates a fresh salt — this is the only moment a salt is created
    for a given vault; it lives inside the file forever after.
    Returns (key, salt) so the caller can keep using them.
    """
    salt = crypto.generate_salt()
    key = crypto.derive_key(password, salt)
    save_vault(path, b"", key, salt)
    return key, salt