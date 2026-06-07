# Requirements — Plugin System

## Acceptance Criteria

### US-01 — Install Plugin
- WHEN a client uploads a plugin ZIP THE SYSTEM SHALL extract, read `manifest.json` + `license.json`, and validate both
- WHEN the license JWT is invalid or expired THE SYSTEM SHALL reject installation with a clear error
- WHEN the client ID in `license.json` does not match the org's client ID THE SYSTEM SHALL reject with 403
- WHEN validation passes THE SYSTEM SHALL register the plugin, inject its routes, and display it in the sidebar

### US-02 — Plugin License Validation
- WHEN a plugin is installed THE SYSTEM SHALL perform phone-home validation of the plugin license
- WHEN the plugin license expires THE SYSTEM SHALL disable the plugin and notify the admin
- THE SYSTEM SHALL re-validate plugin licenses every 24h via a scheduled Celery task

### US-03 — Plugin Management
- WHEN an admin views installed plugins THE SYSTEM SHALL list all plugins with: name, version, license status, expiry date
- WHEN an admin uninstalls a plugin THE SYSTEM SHALL remove its routes and data access (data preserved)

### US-04 — Plugin Isolation
- THE SYSTEM SHALL sandbox each plugin's routes under `/plugins/{plugin_id}/`
- WHEN a plugin calls the core API it SHALL use the authenticated user's token
- WHEN a plugin is disabled its routes SHALL return 503
