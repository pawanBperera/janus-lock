"""
crypto.py — the encryption core of Janus Lock.

Everything here is about turning bytes into other bytes:
  password + salt  ->  key          (derive_key)
  key + plaintext  ->  ciphertext   (encrypt)
  key + ciphertext ->  plaintext    (decrypt)

This module knows NOTHING about files, UI, or vaults.
It only deals in bytes. That separation is deliberate.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

# --- Tunable parameters ---
# Salt and nonce sizes, in bytes. These are standard, well-understood sizes.
SALT_SIZE = 16   # 128 bits — random per vault, stored in plaintext
NONCE_SIZE = 12  # 96 bits  — random per encryption, stored with the ciphertext

# scrypt work factors. Higher = slower for attackers, slower for you too.
# n must be a power of 2. These values are a reasonable 2024-ish default.
SCRYPT_N = 2 ** 15   # CPU/memory cost
SCRYPT_R = 8         # block size
SCRYPT_P = 1         # parallelism
KEY_SIZE = 32        # 32 bytes = 256-bit key for AES-256


def generate_salt() -> bytes:
    """A fresh random salt. Call this ONCE per vault, at creation."""
    return os.urandom(SALT_SIZE)


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Turn a human password into a 256-bit key.

    Why not just use the password directly as the key?
      - Passwords are short and guessable. Keys should be long and random.
      - scrypt makes each guess SLOW and memory-hungry, so brute-forcing
        a password file becomes expensive instead of instant.
    """
    kdf = Scrypt(
        salt=salt,
        length=KEY_SIZE,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt bytes. Returns nonce + ciphertext as one blob.

    AES-GCM is an *authenticated* cipher: if anyone tampers with the
    ciphertext, decryption will FAIL loudly instead of returning garbage.
    That property is why we choose it over older modes like CBC.
    """
    nonce = os.urandom(NONCE_SIZE)          # fresh random nonce per call
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ciphertext               # prepend nonce so we can decrypt


def decrypt(blob: bytes, key: bytes) -> bytes:
    """
    Reverse of encrypt. Raises InvalidTag if the key is wrong
    or the data was tampered with.
    """
    nonce = blob[:NONCE_SIZE]
    ciphertext = blob[NONCE_SIZE:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data=None)