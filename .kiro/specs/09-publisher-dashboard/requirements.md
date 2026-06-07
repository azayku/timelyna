# Requirements — Publisher Dashboard

## Acceptance Criteria

### US-01 — Plugin Management (Publisher)
- WHEN a publisher uploads a plugin ZIP THE SYSTEM SHALL validate it and create a new plugin or new version
- THE SYSTEM SHALL display all plugins with: status, client count, version history

### US-02 — Client Management
- WHEN a publisher onboards a client THE SYSTEM SHALL generate a unique client_id and API key
- THE SYSTEM SHALL display client status, installed plugins, and last validation check

### US-03 — License Generation
- WHEN a publisher creates a license THE SYSTEM SHALL generate a signed RS256 JWT with the configured features/limits
- THE SYSTEM SHALL allow selecting: plugin, client, expiry, features, limits
- WHEN a license is revoked THE SYSTEM SHALL flag it so the next phone-home call rejects it

### US-04 — Release Publishing
- WHEN a publisher creates a release THE SYSTEM SHALL set type (HOTFIX/BUGFIX/FEATURE/CUSTOM) and target (all or specific clients)
- WHEN a release is published THE SYSTEM SHALL notify all targeted clients

### US-05 — Audit & Monitoring
- THE SYSTEM SHALL log every license validation call (client, timestamp, result)
- WHEN a client fails validation 3+ times in 1 hour THE SYSTEM SHALL trigger an alert
- THE SYSTEM SHALL support manual remote audit trigger per client
