"""
StegoVault Core Engine
Provides AES-128 encryption with PBKDF2 key derivation and spatial
RGB Least Significant Bit (LSB) steganography routines.
"""

import base64
import math
import os
import struct
from io import BytesIO
from typing import Dict, Any, Tuple

from PIL import Image
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


SALT_SIZE_BYTES = 16
PBKDF2_ITERATIONS = 480_000
HEADER_BITS = 32


class StegoSecurityError(Exception):
    """Exception raised for cryptographic and steganographic validation failures."""
    pass


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derives a 256-bit URL-safe key using PBKDF2-HMAC-SHA256."""
    if not passphrase:
        raise StegoSecurityError("Passphrase cannot be empty.")
    if len(salt) != SALT_SIZE_BYTES:
        raise StegoSecurityError(f"Salt must be exactly {SALT_SIZE_BYTES} bytes.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def encrypt_message(plaintext: str, passphrase: str) -> Tuple[bytes, bytes]:
    """Encrypts plaintext using Fernet (AES-128-CBC + HMAC-SHA256) with a random salt."""
    if not plaintext:
        raise StegoSecurityError("Secret message cannot be empty.")

    salt = os.urandom(SALT_SIZE_BYTES)
    key = _derive_key(passphrase, salt)
    ciphertext = Fernet(key).encrypt(plaintext.encode("utf-8"))
    return salt, ciphertext


def decrypt_message(salt: bytes, ciphertext: bytes, passphrase: str) -> str:
    """Decrypts ciphertext using derived key. Raises StegoSecurityError if key/data is invalid."""
    try:
        key = _derive_key(passphrase, salt)
        plain = Fernet(key).decrypt(ciphertext)
        return plain.decode("utf-8")
    except InvalidToken:
        raise StegoSecurityError("Decryption failed: Incorrect passphrase or stego-data corrupted.")
    except Exception as e:
        raise StegoSecurityError(f"Decryption error: {str(e)}")


def calculate_capacity(img: Image.Image) -> Dict[str, Any]:
    """Computes usable byte capacity of an RGB image."""
    w, h = img.size
    total_pixels = w * h
    total_bits = total_pixels * 3
    usable_bits = max(0, total_bits - HEADER_BITS)
    max_payload_bytes = usable_bits // 8

    return {
        "width": w,
        "height": h,
        "total_pixels": total_pixels,
        "total_available_bits": total_bits,
        "header_bits": HEADER_BITS,
        "usable_bits": usable_bits,
        "max_payload_bytes": max_payload_bytes,
    }


def _to_bits(data: bytes) -> list:
    """Converts bytes to a flat list of bits (MSB first)."""
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def _from_bits(bits: list) -> bytes:
    """Reconstructs bytes from a list of bits."""
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i : i + 8]:
            byte = (byte << 1) | b
        result.append(byte)
    return bytes(result)


def calculate_psnr(original: Image.Image, stego: Image.Image) -> Tuple[float, float]:
    """Computes Mean Squared Error (MSE) and Peak Signal-to-Noise Ratio (PSNR) in dB."""
    b1 = original.tobytes()
    b2 = stego.tobytes()
    if len(b1) != len(b2) or len(b1) == 0:
        return 0.0, 99.99

    total_sq_diff = 0
    for x, y in zip(b1, b2):
        d = x - y
        total_sq_diff += d * d

    mse = total_sq_diff / len(b1)
    if mse == 0:
        return 0.0, 99.99

    psnr = 10.0 * math.log10((255.0 ** 2) / mse)
    return round(mse, 6), round(psnr, 2)


def encode_lsb(
    image: Image.Image,
    secret_text: str,
    passphrase: str,
) -> Tuple[Image.Image, Dict[str, Any]]:
    """Encodes encrypted payload into the least significant bits of image RGB channels."""
    if image.mode != "RGB":
        image = image.convert("RGB")

    cap = calculate_capacity(image)
    total_channels = cap["total_available_bits"]

    # Encrypt secret text with passphrase
    salt, ciphertext = encrypt_message(secret_text, passphrase)
    payload = salt + ciphertext

    # Pack 32-bit big-endian length prefix header
    header = struct.pack(">I", len(payload))
    full_data = header + payload
    bits = _to_bits(full_data)

    if len(bits) > total_channels:
        raise StegoSecurityError(
            f"Image too small for this message. "
            f"Need {len(bits)} bits but image only provides {total_channels} bits "
            f"({cap['max_payload_bytes']} payload bytes). "
            f"Use a larger image or shorten the message."
        )

    # Embed bits into pixel channels
    px = bytearray(image.tobytes())
    for idx, bit in enumerate(bits):
        px[idx] = (px[idx] & ~1) | bit

    stego = Image.frombytes("RGB", image.size, bytes(px))
    mse, psnr = calculate_psnr(image, stego)

    stats = {
        "image_width": image.size[0],
        "image_height": image.size[1],
        "total_pixels": cap["total_pixels"],
        "total_available_bits": total_channels,
        "payload_length_bytes": len(payload),
        "salt_size_bytes": len(salt),
        "ciphertext_size_bytes": len(ciphertext),
        "total_bits_embedded": len(bits),
        "capacity_used_percent": round(len(bits) / total_channels * 100, 4),
        "mse": mse,
        "psnr_db": psnr,
    }
    return stego, stats


def decode_lsb(
    image: Image.Image,
    passphrase: str,
) -> Tuple[str, Dict[str, Any]]:
    """Extracts and decrypts payload from stego image."""
    if image.mode != "RGB":
        image = image.convert("RGB")

    px = bytearray(image.tobytes())
    total_channels = len(px)

    if total_channels < HEADER_BITS:
        raise StegoSecurityError("Image is too small to contain a valid header.")

    # Read 32-bit payload length header
    header_bits = [px[i] & 1 for i in range(HEADER_BITS)]
    header_bytes = _from_bits(header_bits)
    payload_len = struct.unpack(">I", header_bytes)[0]

    max_payload = (total_channels - HEADER_BITS) // 8
    if payload_len <= 0 or payload_len > max_payload:
        raise StegoSecurityError(
            "No hidden steganographic data detected in this image "
            "(header signature is invalid or the image has not been encoded)."
        )
    if payload_len < SALT_SIZE_BYTES + 1:
        raise StegoSecurityError("Steganographic payload is incomplete or corrupted.")

    # Extract payload bits
    start = HEADER_BITS
    end = start + payload_len * 8
    payload_bits = [px[i] & 1 for i in range(start, end)]
    payload = _from_bits(payload_bits)

    salt = payload[:SALT_SIZE_BYTES]
    ciphertext = payload[SALT_SIZE_BYTES:]

    plaintext = decrypt_message(salt, ciphertext, passphrase)

    stats = {
        "payload_length_bytes": payload_len,
        "salt_size_bytes": len(salt),
        "ciphertext_size_bytes": len(ciphertext),
        "total_bits_extracted": HEADER_BITS + payload_len * 8,
        "algorithm": "AES-128-CBC + HMAC-SHA256 (Fernet) / PBKDF2-HMAC-SHA256",
    }
    return plaintext, stats
