"""FastAPI dependency for module license validation."""
from __future__ import annotations

from datetime import date
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.module_license import ModuleLicense
from app.utils.module_license import validate_key


def require_module_license(module_name: str) -> Callable:
    """
    Create a FastAPI dependency that verifies a specific module license is active and valid.
    
    Args:
        module_name: Name of the module to check (e.g., "finance_pro", "hr_pro")
        
    Returns:
        FastAPI dependency function that raises HTTPException if license is invalid
    """
    async def _check_license(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> None:
        """
        Verify module license is active and valid.
        
        Raises:
            HTTPException: 402 Payment Required if license is invalid, missing, or expired
        """
        org_id = current_user.get("org_id", 1)
        
        # Query module_licenses table for this org and module
        result = await db.execute(
            select(ModuleLicense).where(
                ModuleLicense.org_id == org_id,
                ModuleLicense.module_name == module_name
            )
        )
        module_license = result.scalar_one_or_none()
        
        if not module_license:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"{module_name} license not activated. Please activate a valid license key."
            )
        
        # Validate the license key using the validation utility
        validation_result = validate_key(module_license.license_key)
        
        if not validation_result["valid"]:
            error_msg = validation_result.get("error", "Invalid license")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"{module_name} license invalid: {error_msg}"
            )
        
        # Additional check: verify expiry date matches what's stored in DB
        if module_license.expires_at:
            stored_expiry = module_license.expires_at
            
            # Check if stored expiry date has passed
            if stored_expiry < date.today():
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"{module_name} license expired on {stored_expiry.isoformat()}"
                )
    
    return _check_license


# Convenience function for backward compatibility with Finance Pro
require_finance_license = require_module_license("finance_pro")
