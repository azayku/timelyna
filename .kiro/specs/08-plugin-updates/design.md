# Design — Plugin Updates & Patches

## DB Tables
```sql
CREATE TABLE releases (
  release_id VARCHAR(100) PRIMARY KEY,
  plugin_id VARCHAR(100) NOT NULL,
  version VARCHAR(20) NOT NULL,
  release_type VARCHAR(50) NOT NULL,  -- HOTFIX|BUGFIX|FEATURE|CUSTOM
  severity VARCHAR(50),               -- critical|high|normal
  title VARCHAR(255) NOT NULL,
  release_notes TEXT,
  changelog JSONB,
  target_clients JSONB,               -- null = all, [client_ids] = targeted
  auto_install BOOLEAN DEFAULT false,
  installation_deadline TIMESTAMP,
  file_s3_path VARCHAR(500),
  file_hash VARCHAR(255),
  status VARCHAR(50) DEFAULT 'draft', -- draft|published|archived
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE installation_history (
  id BIGSERIAL PRIMARY KEY,
  release_id VARCHAR(100) REFERENCES releases(release_id),
  org_id VARCHAR(100) NOT NULL,
  plugin_id VARCHAR(100) NOT NULL,
  from_version VARCHAR(20),
  to_version VARCHAR(20),
  status VARCHAR(50),  -- pending|in_progress|completed|failed|rolled_back
  error_message VARCHAR(500),
  backup_s3_path VARCHAR(500),
  data_record_counts JSONB,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Update Check Flow
```
Celery beat: every 6h
  → GET /publisher/plugins/{id}/latest-version per installed plugin
  → If new version available → create notification
  → If HOTFIX/BUGFIX → schedule auto-install Celery task with deadline
```

## Safe Install Process (Celery Task)
```
install_plugin_update(org_id, plugin_id, to_version)
  │
  ├─ 1. Download release ZIP from S3
  ├─ 2. Verify SHA256 checksum
  ├─ 3. Backup: snapshot current plugin data → S3 backup path
  ├─ 4. Record counts before (e.g. invoices: 450)
  ├─ 5. Extract + validate new manifest + license
  ├─ 6. Replace plugin files in S3
  ├─ 7. Run schema migration if needed
  ├─ 8. Verify record counts after (must match or increase)
  ├─ 9. Update installed_plugins record
  ├─ 10. Write installation_history: status=completed
  └─ 11. Notify admin: "Update complete"

On any error:
  ├─ Restore backup
  ├─ Write installation_history: status=failed
  └─ Notify admin: "Update failed, rolled back"
```

## Frontend Components
- `UpdateNotificationBanner.tsx` — sticky critical banner (HOTFIX) with countdown timer
- `UpdatesPage.tsx` — list available updates per plugin with install/schedule/postpone actions
- `InstallProgressModal.tsx` — real-time status polling during installation
- `VersionHistoryPage.tsx` — all versions + rollback button per version
- `RollbackConfirmModal.tsx` — confirms data impact before rollback

# Tasks — Plugin Updates & Patches

- [ ] **8.1** Migration: `releases` table
- [ ] **8.2** Migration: `installation_history` table
- [ ] **8.3** Celery beat task: `check_plugin_updates()` every 6h — calls publisher API per installed plugin
- [ ] **8.4** `UpdateService.schedule_auto_install(release_id, org_id, deadline)` — Celery ETA task
- [ ] **8.5** Celery task: `install_plugin_update(org_id, plugin_id, to_version)` with full safe install steps
- [ ] **8.6** Implement backup step: snapshot plugin data to S3, record counts
- [ ] **8.7** Implement schema migration runner (reads migration scripts from release ZIP)
- [ ] **8.8** Implement rollback: restore S3 backup + revert installed_plugins record
- [ ] **8.9** `GET /api/v1/plugins/updates` — list available updates for org
- [ ] **8.10** `POST /api/v1/plugins/{id}/update` — trigger immediate install
- [ ] **8.11** `POST /api/v1/plugins/{id}/rollback` body: `{ toVersion }`
- [ ] **8.12** `GET /api/v1/plugins/{id}/installation-history`
- [ ] **8.13** Unit test: checksum verification — valid, tampered file
- [ ] **8.14** Unit test: auto-install scheduling — HOTFIX (1h), BUGFIX (48h), FEATURE (no auto)
- [ ] **8.15** Integration test: install → backup → fail → auto-rollback
- [ ] **8.16** Create `UpdateNotificationBanner.tsx` with live countdown (setInterval)
- [ ] **8.17** Create `UpdatesPage.tsx` with install/schedule/postpone actions
- [ ] **8.18** Create `InstallProgressModal.tsx` polling `/installation-history` every 2s
- [ ] **8.19** Create `VersionHistoryPage.tsx` with per-version rollback button
