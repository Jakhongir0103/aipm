import base64
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

SECRET_KEY = os.environ["SECRET_TOKEN_ENCRYPTION_KEY"][
    :32
]  # AES-256 requires 32-byte key
PREFIX = b"TIMESTAMP"  # Adding a constant prefix


def encrypt_timestamp(timestamp_int: int) -> str:
    cipher = AES.new(SECRET_KEY.encode(), AES.MODE_ECB)
    timestamp_bytes = timestamp_int.to_bytes(
        8, byteorder="big"
    )  # 8 bytes for timestamp
    prefixed_data = PREFIX + timestamp_bytes  # Combine prefix with timestamp
    padded_data = pad(prefixed_data, AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    token = base64.urlsafe_b64encode(encrypted).decode()
    return token


def decrypt_timestamp(token: str):
    cipher = AES.new(SECRET_KEY.encode(), AES.MODE_ECB)
    encrypted = base64.urlsafe_b64decode(token.encode())
    decrypted_padded = cipher.decrypt(encrypted)
    timestamp_bytes = unpad(decrypted_padded, AES.block_size)
    # Verify and remove prefix
    if not timestamp_bytes.startswith(PREFIX):
        raise ValueError("Invalid token: incorrect prefix")
    timestamp_bytes = timestamp_bytes[len(PREFIX) :]  # Remove prefix
    timestamp_int = int.from_bytes(timestamp_bytes, byteorder="big")
    return timestamp_int
