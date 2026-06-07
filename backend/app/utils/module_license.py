"""Module license key generation and validation using HMAC-SHA256 + XOR + CRC32."""
from __future__ import annotations

import hmac
import hashlib
import struct
import zlib
from datetime import date, datetime
from typing import TypedDict

from app.core.config import get_settings


class ValidationResult(TypedDict):
    """Result of license key validation."""
    valid: bool
    expiry_date: date | None
    error: str | None


def _base36_encode(number: int) -> str:
    """Encode a positive integer to base36 string."""
    if number == 0:
        return "0"
    
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = []
    
    while number:
        number, remainder = divmod(number, 36)
        result.append(alphabet[remainder])
    
    return "".join(reversed(result))


def _base36_decode(encoded: str) -> int:
    """Decode a base36 string to integer."""
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return sum(alphabet.index(char) * (36 ** idx) for idx, char in enumerate(reversed(encoded.upper())))


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """Apply XOR obfuscation to data using key."""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def generate_key(expiry: date) -> str:
    """
    Generate a module license key.
    
    Format: HMAC-SHA256(expiry_timestamp) + XOR obfuscation + CRC32 checksum, encoded in base36.
    
    Args:
        expiry: Expiration date for the license
        
    Returns:
        License key string in base36 format
    """
    settings = get_settings()
    secret = settings.FINANCE_LICENSE_SECRET.encode("utf-8")
    
    # Convert expiry date to timestamp (days since epoch)
    epoch = date(1970, 1, 1)
    days_since_epoch = (expiry - epoch).days
    
    # Create payload: 4 bytes for timestamp
    payload = struct.pack(">I", days_since_epoch)
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(secret, payload, hashlib.sha256).digest()
    
    # Take first 16 bytes of signature for compactness
    signature_truncated = signature[:16]
    
    # Combine payload + signature
    combined = payload + signature_truncated
    
    # Apply XOR obfuscation using first 8 bytes of secret as XOR key
    xor_key = hashlib.sha256(secret).digest()[:8]
    obfuscated = _xor_bytes(combined, xor_key)
    
    # Calculate CRC32 checksum
    checksum = zlib.crc32(obfuscated) & 0xFFFFFFFF
    
    # Combine obfuscated data + checksum (4 bytes)
    final_data = obfuscated + struct.pack(">I", checksum)
    
    # Convert to integer and encode in base36
    data_int = int.from_bytes(final_data, byteorder="big")
    key = _base36_encode(data_int)
    
    # Add dashes for readability (every 5 characters)
    formatted_key = "-".join(key[i:i+5] for i in range(0, len(key), 5))
    
    return formatted_key


def validate_key(key: str) -> ValidationResult:
    """
    Validate a module license key.
    
    Args:
        key: License key string to validate
        
    Returns:
        ValidationResult dict with:
            - valid: True if key is valid and not expired
            - expiry_date: Expiration date if valid, None otherwise
            - error: Error message if invalid, None otherwise
    """
    settings = get_settings()
    secret = settings.FINANCE_LICENSE_SECRET.encode("utf-8")
    
    try:
        # Remove dashes and whitespace
        clean_key = key.replace("-", "").replace(" ", "").upper()
        
        if not clean_key:
            return {"valid": False, "expiry_date": None, "error": "Empty key"}
        
        # Decode from base36
        try:
            data_int = _base36_decode(clean_key)
        except (ValueError, KeyError):
            return {"valid": False, "expiry_date": None, "error": "Invalid key format"}
        
        # Convert back to bytes
        # Expected length: 4 (payload) + 16 (signature) + 4 (checksum) = 24 bytes
        final_data = data_int.to_bytes((data_int.bit_length() + 7) // 8, byteorder="big")
        
        if len(final_data) != 24:
            return {"valid": False, "expiry_date": None, "error": "Invalid key length"}
        
        # Split checksum and obfuscated data
        obfuscated = final_data[:20]
        checksum_bytes = final_data[20:]
        checksum = struct.unpack(">I", checksum_bytes)[0]
        
        # Verify CRC32 checksum
        calculated_checksum = zlib.crc32(obfuscated) & 0xFFFFFFFF
        if checksum != calculated_checksum:
            return {"valid": False, "expiry_date": None, "error": "Checksum verification failed"}
        
        # Remove XOR obfuscation
        xor_key = hashlib.sha256(secret).digest()[:8]
        deobfuscated = _xor_bytes(obfuscated, xor_key)
        
        # Split payload and signature
        payload = deobfuscated[:4]
        signature_received = deobfuscated[4:]
        
        # Verify HMAC signature
        expected_signature = hmac.new(secret, payload, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(signature_received, expected_signature):
            return {"valid": False, "expiry_date": None, "error": "Invalid signature"}
        
        # Extract expiry date
        days_since_epoch = struct.unpack(">I", payload)[0]
        epoch = date(1970, 1, 1)
        expiry_date = epoch.replace(year=epoch.year + days_since_epoch // 365)
        # More accurate calculation
        from datetime import timedelta
        expiry_date = epoch + timedelta(days=days_since_epoch)
        
        # Check if expired
        today = date.today()
        if expiry_date < today:
            return {
                "valid": False,
                "expiry_date": expiry_date,
                "error": f"License expired on {expiry_date.isoformat()}"
            }
        
        return {"valid": True, "expiry_date": expiry_date, "error": None}
        
    except Exception as e:
        return {"valid": False, "expiry_date": None, "error": f"Validation error: {str(e)}"}
