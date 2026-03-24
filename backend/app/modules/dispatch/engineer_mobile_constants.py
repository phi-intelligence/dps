"""Engineer mobile ↔ dispatch API guardrails (Wave 7)."""

# Aligns with mobile JSON payload size guard for base64-heavy photo uploads.
ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES = 2 * 1024 * 1024
