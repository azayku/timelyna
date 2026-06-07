"""License-related exception hierarchy."""
from __future__ import annotations


class LicenseError(Exception):
    pass


class LicenseExpiredError(LicenseError):
    pass


class LicenseRevokedError(LicenseError):
    pass


class LicenseInvalidError(LicenseError):
    pass


class LicenseFeatureError(LicenseError):
    def __init__(self, feature: str) -> None:
        self.feature = feature
        super().__init__(f"Feature not included in license: {feature}")


class LicenseLimitError(LicenseError):
    def __init__(self, resource: str, current: int, max_val: int) -> None:
        self.resource = resource
        self.current = current
        self.max_val = max_val
        super().__init__(f"Limit exceeded for {resource}: {current}/{max_val}")
