#!/usr/bin/env python
"""Test d'import des modules entry_templates."""

try:
    from app.models.entry_template import EntryTemplate
    print("✓ Modèle EntryTemplate importé")
except Exception as e:
    print(f"✗ Erreur modèle : {e}")
    exit(1)

try:
    from app.schemas.entry_template import EntryTemplateCreate, EntryTemplateUpdate, EntryTemplateResponse
    print("✓ Schémas entry_template importés")
except Exception as e:
    print(f"✗ Erreur schémas : {e}")
    exit(1)

try:
    from app.api.v1.entry_templates import router
    print(f"✓ Router entry_templates importé ({len(router.routes)} routes)")
except Exception as e:
    print(f"✗ Erreur router : {e}")
    exit(1)

try:
    from app.main import app
    routes = [r for r in app.routes if 'entry-templates' in str(r.path)]
    print(f"✓ Application principale OK ({len(routes)} routes entry-templates)")
    
    # Afficher les routes
    print("\nRoutes disponibles:")
    for route in routes:
        print(f"  - {route.methods} {route.path}")
    
except Exception as e:
    print(f"✗ Erreur app : {e}")
    exit(1)

print("\n✅ Tous les tests d'import réussis!")
