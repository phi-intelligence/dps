# Wave 4 — Engineer evidence submission (mobile)

## Implemented (backend-aligned)

| Flow | Endpoint | Notes |
|------|----------|--------|
| Forms / checklists | `POST /jobs/{id}/forms/{form_key}/submit` | Body `{ "data": { ... } }`. Keys must satisfy `required_keys_json` when a requirement row exists. |
| Signature | `POST /jobs/{id}/signature` | Body `{ "signature": { ... } }`. Mobile sends PNG as base64 with `encoding: png_base64` plus metadata — **not** multipart. |
| Media / photos | `POST /jobs/{id}/media` | Body `{ "media_type": "photo", "payloads": [ ... ] }`. Each payload is JSON (e.g. `content_base64`, `filename`, `mime_type`). Server counts **cumulative** photo rows vs `required_photo_count`. |
| Parts usage | `POST /jobs/{id}/parts-usage` | Body `{ "items": [ { "sku", "quantity", ... } ] }`. **SKUs must exist in inventory** or the API returns HTTP 400. |

## Blockers / limitations (no invented APIs)

- **Engineer job notes:** No `POST /jobs/{id}/notes` — notes UI stays disabled.
- **Certificates:** Admin/Dispatcher-only in current API — no engineer actions.
- **Media transport:** JSON base64 is practical for a first pass but can hit **request body size** limits on large images or many photos; production may need multipart + presigned URLs or chunked upload (backend change).
- **Parts + material policy:** When `material_policy == no_materials_expected`, the app **does not** show a parts submit button (requirement rows may still display for reference).

## Refresh contract

After a successful submission route (`Navigator.pop(true)`), `JobDetailScreen` calls `_refreshJob()` which:

1. Invalidates `jobGeofenceProvider` and `completionRequirementsProvider`
2. Fetches fresh job via `jobsRepository.getJob`

## Future (Wave 5+)

- Offline queue wrapping `JobEvidenceRepository` methods
- Retry policies, compression presets for media, inventory SKU lookup/picker if API exposes it
