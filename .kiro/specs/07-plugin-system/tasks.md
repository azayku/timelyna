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
