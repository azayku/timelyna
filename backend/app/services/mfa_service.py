"""MFA/2FA TOTP service for Google Authenticator / Authy compatibility."""
from __future__ import annotations

import base64
import io
import logging
from typing import TYPE_CHECKING

import pyotp
import qrcode

if TYPE_CHECKING:
    from PIL.Image import Image

logger = logging.getLogger(__name__)


class MFAService:
    """Service for managing TOTP-based multi-factor authentication."""

    def generate_secret(self) -> str:
        """Generate a new TOTP secret (base32 encoded)."""
        return pyotp.random_base32()

    def get_totp_uri(self, secret: str, user_email: str, issuer: str = "Timelyna") -> str:
        """Generate provisioning URI for QR code scanning.

        Args:
            secret: Base32-encoded TOTP secret
            user_email: User's email address (displayed in authenticator app)
            issuer: Application name (default: Timelyna)

        Returns:
            otpauth:// URI string
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer)

    def generate_qr_base64(self, totp_uri: str) -> str:
        """Generate base64-encoded PNG QR code from TOTP URI.

        Args:
            totp_uri: The otpauth:// URI

        Returns:
            Base64-encoded PNG image string
        """
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        img: Image = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode()

    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify a TOTP code against the secret.

        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit code from authenticator app

        Returns:
            True if code is valid (with ±1 time window tolerance)
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
