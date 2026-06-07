# Requirements — Plugin Updates & Patches

## Acceptance Criteria

### US-01 — Update Notification
- WHEN a new release is available THE SYSTEM SHALL notify the admin in-app and via email
- WHEN release type is HOTFIX THE SYSTEM SHALL display a critical banner with countdown
- WHEN release type is FEATURE THE SYSTEM SHALL show a non-urgent notification (no auto-install)

### US-02 — Auto-Install (HOTFIX/BUGFIX)
- WHEN a HOTFIX is published THE SYSTEM SHALL auto-install after 1 hour if not manually installed (max 3 postponements)
- WHEN a BUGFIX is published THE SYSTEM SHALL auto-install after 48 hours if not manually installed

### US-03 — Safe Installation
- WHEN any update is installed THE SYSTEM SHALL backup current plugin data before replacing
- WHEN installation fails THE SYSTEM SHALL automatically rollback to the previous version
- WHEN installation succeeds THE SYSTEM SHALL verify data integrity (record counts, schema check)

### US-04 — Rollback
- WHEN an admin initiates rollback THE SYSTEM SHALL restore the previous plugin version and data backup
- THE SYSTEM SHALL keep the last 3 versions available for rollback

### US-05 — Custom Patches
- WHEN a custom patch is deployed (publisher-initiated) THE SYSTEM SHALL only be visible to the target client
- THE SYSTEM SHALL use a unique license for each custom patch version
