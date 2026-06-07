"""Unit tests for module license key validation."""
import pytest
from datetime import date, timedelta
import struct

from app.utils.module_license import generate_key, validate_key


class TestValidateKey:
    """Unit tests for validate_key function."""
    
    def test_valid_key_future_expiry(self):
        """Test that a valid key with future expiry date returns valid=True."""
        expiry = date.today() + timedelta(days=365)
        key = generate_key(expiry)
        
        result = validate_key(key)
        
        assert result["valid"] is True
        assert result["expiry_date"] == expiry
        assert result["error"] is None
    
    def test_invalid_format_random_string(self):
        """Test that an invalid format (random string) returns valid=False with error."""
        result = validate_key("INVALID-KEY-12345")
        
        assert result["valid"] is False
        assert result["expiry_date"] is None
        assert result["error"] is not None
        assert "invalid" in result["error"].lower() or "format" in result["error"].lower()
    
    def test_invalid_format_empty_key(self):
        """Test that an empty key returns valid=False with error."""
        result = validate_key("")
        
        assert result["valid"] is False
        assert result["expiry_date"] is None
        assert result["error"] == "Empty key"
    
    def test_tampered_checksum(self):
        """Test that a key with tampered checksum returns valid=False with checksum error."""
        expiry = date.today() + timedelta(days=365)
        key = generate_key(expiry)
        
        # Tamper with the key by changing a character
        tampered_key = key[:-1] + ("X" if key[-1] != "X" else "Y")
        
        result = validate_key(tampered_key)
        
        assert result["valid"] is False
        assert result["expiry_date"] is None
        assert result["error"] is not None
        # Should fail at checksum or format validation
        assert any(word in result["error"].lower() for word in ["checksum", "invalid", "format", "length"])
    
    def test_invalid_hmac_signature(self):
        """Test that a key with invalid HMAC signature returns valid=False with signature error."""
        # Generate a valid key
        expiry = date.today() + timedelta(days=365)
        key = generate_key(expiry)
        
        # We need to create a key with valid structure but wrong HMAC
        # This is tricky because we need to maintain checksum but break HMAC
        # The easiest way is to modify the secret temporarily during validation
        # But since we can't do that, we'll create a key with a different secret
        
        # Alternative: manually construct a key with wrong signature
        from app.utils.module_license import _base36_encode, _base36_decode, _xor_bytes
        import hashlib
        import hmac
        import zlib
        from app.core.config import get_settings
        
        settings = get_settings()
        secret = settings.FINANCE_LICENSE_SECRET.encode("utf-8")
        wrong_secret = b"wrong_secret_key_for_testing"
        
        # Create payload
        epoch = date(1970, 1, 1)
        days_since_epoch = (expiry - epoch).days
        payload = struct.pack(">I", days_since_epoch)
        
        # Generate WRONG signature
        wrong_signature = hmac.new(wrong_secret, payload, hashlib.sha256).digest()[:16]
        
        # Combine with correct XOR key
        combined = payload + wrong_signature
        xor_key = hashlib.sha256(secret).digest()[:8]
        obfuscated = _xor_bytes(combined, xor_key)
        
        # Calculate correct checksum (so it passes checksum validation)
        checksum = zlib.crc32(obfuscated) & 0xFFFFFFFF
        final_data = obfuscated + struct.pack(">I", checksum)
        
        # Encode
        data_int = int.from_bytes(final_data, byteorder="big")
        invalid_key = _base36_encode(data_int)
        formatted_key = "-".join(invalid_key[i:i+5] for i in range(0, len(invalid_key), 5))
        
        result = validate_key(formatted_key)
        
        assert result["valid"] is False
        assert result["expiry_date"] is None
        assert result["error"] is not None
        assert "signature" in result["error"].lower()
    
    def test_expired_key(self):
        """Test that an expired key returns valid=False with expired error."""
        # Generate a key that expired yesterday
        expiry = date.today() - timedelta(days=1)
        key = generate_key(expiry)
        
        result = validate_key(key)
        
        assert result["valid"] is False
        assert result["expiry_date"] == expiry
        assert result["error"] is not None
        assert "expired" in result["error"].lower()
    
    def test_key_with_whitespace(self):
        """Test that keys with whitespace are handled correctly."""
        expiry = date.today() + timedelta(days=365)
        key = generate_key(expiry)
        
        # Add whitespace
        key_with_spaces = "  " + key + "  "
        
        result = validate_key(key_with_spaces)
        
        assert result["valid"] is True
        assert result["expiry_date"] == expiry
        assert result["error"] is None
    
    def test_key_without_dashes(self):
        """Test that keys without dashes are handled correctly."""
        expiry = date.today() + timedelta(days=365)
        key = generate_key(expiry)
        
        # Remove dashes
        key_no_dashes = key.replace("-", "")
        
        result = validate_key(key_no_dashes)
        
        assert result["valid"] is True
        assert result["expiry_date"] == expiry
        assert result["error"] is None
