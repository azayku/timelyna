# Design — Plugin System

## Plugin ZIP Structure
```
plugin.zip
├── manifest.json     ← plugin metadata, permissions, routes
├── license.json      ← JWT license per-client
├── src/index.jsx     ← React entry point
└── ...
```

## DB Tables
```sql
CREATE TABLE installed_plugins (
  id BIGSERIAL PRIMARY KEY,
  org_id VARCHAR(100) NOT NULL,
  plugin_id VARCHAR(100) NOT NULL,
  plugin_name VARCHAR(255) NOT NULL,
  version VARCHAR(20) NOT NULL,
  manifest JSONB NOT NULL,
  license_token TEXT NOT NULL,
  license_expires_at TIMESTAMP,
  license_status VARCHAR(50) DEFAULT 'active',  -- active|expired|revoked|disabled
  installed_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (org_id, plugin_id)
);
```

## Installation Flow (Backend)
```
POST /api/v1/plugins/install  (multipart ZIP)
  │
  ├─ Extract ZIP to temp dir
  ├─ Parse + validate manifest.json (required fields, version compat)
  ├─ Parse + validate license.json JWT (RS256 signature, expiry, client_id match)
  ├─ POST phone-home: /publisher/license/validate
  ├─ Store plugin record in installed_plugins
  ├─ Store plugin files to S3 (org_id/plugin_id/version/)
  └─ Return plugin manifest to frontend
```

## Frontend Plugin Loader
```typescript
// Plugin routes are injected dynamically at runtime
const pluginRoutes = installedPlugins.map(plugin => ({
  path: `/plugins/${plugin.plugin_id}/*`,
  element: <PluginHost pluginId={plugin.plugin_id} />,
}));

// PluginHost loads the plugin's index.jsx from S3 via dynamic import
const PluginHost = ({ pluginId }) => {
  const [Component, setComponent] = useState(null);
  useEffect(() => {
    import(/* @vite-ignore */ `/api/v1/plugins/${pluginId}/bundle.js`)
      .then(mod => setComponent(() => mod.default));
  }, [pluginId]);
  return Component ? <Component /> : <PluginLoadingSpinner />;
};
```

## API Endpoints
```
POST   /api/v1/plugins/install               multipart ZIP upload
GET    /api/v1/plugins                       list installed plugins
DELETE /api/v1/plugins/{plugin_id}           uninstall
GET    /api/v1/plugins/{plugin_id}/bundle.js serve compiled JS to frontend
POST   /api/v1/plugins/{plugin_id}/disable
POST   /api/v1/plugins/{plugin_id}/enable
```

## Scheduled License Re-validation
```
Celery beat: every 24h
  → for each active installed_plugin
    → validate license JWT (expiry)
    → phone-home validate
    → if invalid → set license_status = 'expired' + notify admin
```

# Tasks — Plugin System

- [ ] **7.1** Migration: `installed_plugins` table
- [ ] **7.2** `PluginService.install(org_id, zip_file)` — extract, validate manifest + license JWT, phone-home, store to S3
- [ ] **7.3** `PluginService.uninstall(org_id, plugin_id)` — remove DB record + S3 files (preserve data tables)
- [ ] **7.4** `PluginService.validate_license(plugin_id)` — local JWT check + phone-home
- [ ] **7.5** Celery beat task: `revalidate_all_plugin_licenses()` every 24h
- [ ] **7.6** `GET /api/v1/plugins/{plugin_id}/bundle.js` — serve compiled plugin JS from S3
- [ ] **7.7** Register all plugin management API routes with `require_role('admin')`
- [ ] **7.8** Unit test: install — valid ZIP, bad manifest, invalid license JWT, wrong client_id
- [ ] **7.9** Unit test: license re-validation — active, expired, revoked
- [ ] **7.10** Create `PluginManagerPage.tsx` — installed plugins list with status badges + install/uninstall
- [ ] **7.11** Create `PluginInstallModal.tsx` — drag & drop ZIP upload with validation feedback
- [ ] **7.12** Create `PluginHost.tsx` — dynamic import loader with error boundary
- [ ] **7.13** Inject plugin routes into React Router dynamically from `useInstalledPlugins` hook
- [ ] **7.14** Add plugin nav items to sidebar from installed plugin manifests
