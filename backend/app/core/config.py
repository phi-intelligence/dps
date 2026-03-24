import os


class Settings:
    """
    Lightweight settings loader to keep the repo bootstrap simple.
    In later phases, swap to pydantic-settings or your preferred config system.
    """

    # Auth
    SECRET_KEY: str = os.getenv("PHI_DPS_SECRET_KEY", "dev-secret-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("PHI_DPS_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = os.getenv("PHI_DPS_ALGORITHM", "HS256")

    # DB
    DATABASE_URL: str = os.getenv("PHI_DPS_DATABASE_URL", "sqlite:///./dev.db")

    # CORS
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv(
            "PHI_DPS_CORS_ORIGINS",
            # Allow both common dev origins so the browser can talk to the backend.
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if o.strip()
    ]

    # Notifications/webhooks
    NOTIFICATION_WEBHOOK_SECRET: str = os.getenv("PHI_DPS_NOTIFICATION_WEBHOOK_SECRET", "dev-webhook-secret")

    # Inventory / field execution (start-4)
    # When true, jobs with parts usage exceptions (overuse / unreserved / unavailable) cannot
    # complete until dispatcher/admin approves reconciliation.
    STRICT_PARTS_RECONCILIATION: bool = os.getenv("PHI_DPS_STRICT_PARTS_RECONCILIATION", "0") == "1"

    # Dispatch / telemetry intelligence
    PHI_DPS_TELEMETRY_FRESH_SECONDS: float = float(os.getenv("PHI_DPS_TELEMETRY_FRESH_SECONDS", "60"))
    PHI_DPS_TELEMETRY_AGING_SECONDS: float = float(os.getenv("PHI_DPS_TELEMETRY_AGING_SECONDS", "300"))
    # freshest | vehicle_preferred | phone_preferred
    PHI_DPS_OPERATIONAL_POSITION_MODE: str = os.getenv("PHI_DPS_OPERATIONAL_POSITION_MODE", "freshest")
    PHI_DPS_DISPATCH_RECOMMEND_STALE: bool = os.getenv("PHI_DPS_DISPATCH_RECOMMEND_STALE", "0") == "1"
    PHI_DPS_AVG_VEHICLE_SPEED_MPS: float = float(os.getenv("PHI_DPS_AVG_VEHICLE_SPEED_MPS", "13.89"))

    # Portal / customer comms (display-only defaults; wire to real support desk later)
    PORTAL_SUPPORT_EMAIL: str = os.getenv("PHI_DPS_PORTAL_SUPPORT_EMAIL", "support@example.com")
    PORTAL_SUPPORT_PHONE: str = os.getenv("PHI_DPS_PORTAL_SUPPORT_PHONE", "+44 20 0000 0000")
    # Customer-facing links in generated communications (web app origin; not the API host).
    PHI_DPS_PORTAL_WEB_BASE: str = os.getenv("PHI_DPS_PORTAL_WEB_BASE", "http://127.0.0.1:3000").rstrip("/")

    # Outbound customer communications (email first; SMS later). Secrets stay in env only.
    COMMUNICATION_ENABLED: bool = os.getenv("PHI_DPS_COMMUNICATION_ENABLED", "0") == "1"
    # none | smtp | sendgrid — none uses in-process simulation (still writes delivery rows; no network).
    COMMUNICATION_EMAIL_PROVIDER: str = os.getenv("PHI_DPS_COMMUNICATION_EMAIL_PROVIDER", "none").strip().lower()
    SENDGRID_API_KEY: str = os.getenv("PHI_DPS_SENDGRID_API_KEY", "").strip()
    # Shared secret for POST /webhooks/communications/sendgrid-events (header X-Phi-Dps-Sendgrid-Ingest-Secret)
    SENDGRID_WEBHOOK_INGEST_SECRET: str = os.getenv("PHI_DPS_SENDGRID_WEBHOOK_INGEST_SECRET", "").strip()
    # Optional JSON map: {"repricing_proposal_reminder":"sms"} overrides template default channel for new comm rows.
    COMMUNICATION_TYPE_CHANNEL_MAP_JSON: str = os.getenv("PHI_DPS_COMMUNICATION_TYPE_CHANNEL_MAP_JSON", "").strip()
    # none | twilio | simulated — SMS outbound for contract comms channel=sms (simulated when disabled/none).
    COMMUNICATION_SMS_PROVIDER: str = os.getenv("PHI_DPS_COMMUNICATION_SMS_PROVIDER", "none").strip().lower()
    TWILIO_ACCOUNT_SID: str = os.getenv("PHI_DPS_TWILIO_ACCOUNT_SID", "").strip()
    TWILIO_AUTH_TOKEN: str = os.getenv("PHI_DPS_TWILIO_AUTH_TOKEN", "").strip()
    TWILIO_FROM_NUMBER: str = os.getenv("PHI_DPS_TWILIO_FROM_NUMBER", "").strip()

    # §5.17 — customer communication templates (versioned keys + en/fr copy in code)
    COMMUNICATION_TEMPLATE_LOCALE: str = os.getenv("PHI_DPS_COMMUNICATION_TEMPLATE_LOCALE", "en").strip()
    COMMUNICATION_TEMPLATE_CATALOG_VERSION: str = os.getenv(
        "PHI_DPS_COMMUNICATION_TEMPLATE_CATALOG_VERSION", "1"
    ).strip()
    SMTP_HOST: str = os.getenv("PHI_DPS_SMTP_HOST", "").strip()
    SMTP_PORT: int = int(os.getenv("PHI_DPS_SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("PHI_DPS_SMTP_USERNAME", "").strip()
    SMTP_PASSWORD: str = os.getenv("PHI_DPS_SMTP_PASSWORD", "").strip()
    SMTP_USE_TLS: bool = os.getenv("PHI_DPS_SMTP_USE_TLS", "1") == "1"
    COMMUNICATION_FROM_EMAIL: str = os.getenv("PHI_DPS_COMMUNICATION_FROM_EMAIL", "").strip()
    COMMUNICATION_FROM_NAME: str = os.getenv("PHI_DPS_COMMUNICATION_FROM_NAME", "PHI-DPS").strip()
    COMMUNICATION_REPLY_TO: str = os.getenv("PHI_DPS_COMMUNICATION_REPLY_TO", "").strip()
    # HMAC secret for POST /webhooks/communications/* (provider delivery callbacks)
    COMMUNICATION_WEBHOOK_SECRET: str = os.getenv(
        "PHI_DPS_COMMUNICATION_WEBHOOK_SECRET", "dev-comm-webhook-secret"
    )

    # Ops recommendations
    PHI_DPS_CONTRACT_RENEWAL_SCAN_DAYS: int = int(os.getenv("PHI_DPS_CONTRACT_RENEWAL_SCAN_DAYS", "90"))
    PHI_DPS_CONTRACT_OVERDUE_INVOICE_DAYS: int = int(os.getenv("PHI_DPS_CONTRACT_OVERDUE_INVOICE_DAYS", "30"))
    PHI_DPS_OPS_RECOMMENDATION_RULE_VERSION: str = os.getenv("PHI_DPS_OPS_RECOMMENDATION_RULE_VERSION", "2025.03.v1")
    # Lifecycle: cooldown before a new open row after close (manual reopen bypasses).
    PHI_DPS_OPS_REC_COOLDOWN_DISMISS_HOURS: float = float(os.getenv("PHI_DPS_OPS_REC_COOLDOWN_DISMISS_HOURS", "24"))
    PHI_DPS_OPS_REC_COOLDOWN_RESOLVE_HOURS: float = float(os.getenv("PHI_DPS_OPS_REC_COOLDOWN_RESOLVE_HOURS", "6"))
    # Repeated fires of the same recommendation_key in this window → one severity bump.
    PHI_DPS_OPS_REC_ESCALATION_WINDOW_HOURS: float = float(os.getenv("PHI_DPS_OPS_REC_ESCALATION_WINDOW_HOURS", "168"))
    PHI_DPS_OPS_REC_ESCALATION_MIN_FIRES: int = int(os.getenv("PHI_DPS_OPS_REC_ESCALATION_MIN_FIRES", "5"))
    PHI_DPS_OPS_REC_ESCALATION_ENABLED: bool = os.getenv("PHI_DPS_OPS_REC_ESCALATION_ENABLED", "1") == "1"

    # Labour costing (fallback when no LabourRateProfile row; profiles are model-driven in DB)
    PHI_DPS_LABOUR_HOURLY_RATE: float = float(os.getenv("PHI_DPS_LABOUR_HOURLY_RATE", "60"))
    PHI_DPS_OVERTIME_MULTIPLIER: float = float(os.getenv("PHI_DPS_OVERTIME_MULTIPLIER", "1.5"))

    # Document storage (local dev default; S3-compatible for production)
    PHI_DPS_DOCUMENT_STORAGE_PROVIDER: str = os.getenv("PHI_DPS_DOCUMENT_STORAGE_PROVIDER", "local")
    PHI_DPS_DOCUMENT_STORAGE_ROOT: str = os.getenv("PHI_DPS_DOCUMENT_STORAGE_ROOT", "var/phi_dps_documents")
    PHI_DPS_DOCUMENT_DOWNLOAD_TOKEN_TTL_SECONDS: int = int(os.getenv("PHI_DPS_DOCUMENT_DOWNLOAD_TOKEN_TTL_SECONDS", "300"))
    # S3-compatible (MinIO, AWS, etc.) — only used when PHI_DPS_DOCUMENT_STORAGE_PROVIDER=s3
    PHI_DPS_S3_BUCKET: str = os.getenv("PHI_DPS_S3_BUCKET", "")
    PHI_DPS_S3_REGION: str = os.getenv("PHI_DPS_S3_REGION", "us-east-1")
    PHI_DPS_S3_ENDPOINT_URL: str | None = os.getenv("PHI_DPS_S3_ENDPOINT_URL") or None
    PHI_DPS_S3_ACCESS_KEY_ID: str | None = os.getenv("PHI_DPS_S3_ACCESS_KEY_ID") or None
    PHI_DPS_S3_SECRET_ACCESS_KEY: str | None = os.getenv("PHI_DPS_S3_SECRET_ACCESS_KEY") or None
    PHI_DPS_S3_PREFIX: str = os.getenv("PHI_DPS_S3_PREFIX", "phi-dps-documents").strip().strip("/")
    # path | virtual — path-style for many MinIO setups
    PHI_DPS_S3_ADDRESSING_STYLE: str = os.getenv("PHI_DPS_S3_ADDRESSING_STYLE", "path")
    PHI_DPS_S3_PRESIGNED_TTL_SECONDS: int = int(os.getenv("PHI_DPS_S3_PRESIGNED_TTL_SECONDS", "300"))
    # PDF / branding (invoice & certificate headers)
    PHI_DPS_COMPANY_NAME: str = os.getenv("PHI_DPS_COMPANY_NAME", "PHI-DPS Service Ltd")
    PHI_DPS_COMPANY_TAGLINE: str = os.getenv("PHI_DPS_COMPANY_TAGLINE", "Field service & compliance")
    PHI_DPS_COMPANY_ADDRESS: str = os.getenv("PHI_DPS_COMPANY_ADDRESS", "United Kingdom")

    # Field equipment / calibration readiness
    PHI_DPS_EQUIPMENT_CALIBRATION_DUE_SOON_DAYS: int = int(os.getenv("PHI_DPS_EQUIPMENT_CALIBRATION_DUE_SOON_DAYS", "30"))

    # --- AI provider (Gemini) — read from environment at access time (supports tests / reload). ---

    @property
    def GEMINI_ENABLED(self) -> bool:
        return os.getenv("GEMINI_ENABLED", "0") == "1"

    @property
    def GEMINI_API_KEY(self) -> str:
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    @property
    def GEMINI_BASE_URL(self) -> str:
        return (os.getenv("GEMINI_BASE_URL") or "").strip()

    @property
    def AI_ASSISTED_DRAFTING_ENABLED(self) -> bool:
        """§5.19 — second gate for LLM drafting APIs (in addition to GEMINI_* and RBAC)."""
        return os.getenv("PHI_DPS_AI_ASSISTED_DRAFTING_ENABLED", "0") == "1"

    # --- Legal e-sign (third-party) — secrets and IDs from env only; never log or return in API. ---
    @property
    def ESIGN_ENABLED(self) -> bool:
        return os.getenv("PHI_DPS_ESIGN_ENABLED", "0") == "1"

    @property
    def ESIGN_PROVIDER(self) -> str:
        return (os.getenv("PHI_DPS_ESIGN_PROVIDER", "stub") or "stub").strip().lower()

    @property
    def ESIGN_FALLBACK_PROVIDER(self) -> str:
        """When primary e-sign provider is not configured, use this if set (e.g. ``stub`` or ``echo``). §5.16."""
        return (os.getenv("PHI_DPS_ESIGN_FALLBACK_PROVIDER") or "").strip().lower()

    @property
    def ESIGN_API_KEY(self) -> str:
        """Integration key / client id fallback when PHI_DPS_ESIGN_CLIENT_ID is unset."""
        return os.getenv("PHI_DPS_ESIGN_API_KEY", "").strip()

    @property
    def ESIGN_CLIENT_ID(self) -> str:
        return os.getenv("PHI_DPS_ESIGN_CLIENT_ID", "").strip()

    @property
    def ESIGN_USER_ID(self) -> str:
        """DocuSign user GUID (impersonated) for JWT grant."""
        return os.getenv("PHI_DPS_ESIGN_USER_ID", "").strip()

    @property
    def ESIGN_RSA_PRIVATE_KEY_PATH(self) -> str:
        """Path to PEM RSA private key for DocuSign JWT (never commit real keys)."""
        return os.getenv("PHI_DPS_ESIGN_RSA_PRIVATE_KEY_PATH", "").strip()

    @property
    def ESIGN_AUTH_SERVER(self) -> str:
        """OAuth host, e.g. account-d.docusign.com (demo) or account.docusign.com."""
        return (os.getenv("PHI_DPS_ESIGN_AUTH_SERVER") or "account-d.docusign.com").strip()

    @property
    def ESIGN_BASE_URL(self) -> str:
        """REST API origin, e.g. https://demo.docusign.net/restapi"""
        return (os.getenv("PHI_DPS_ESIGN_BASE_URL") or "").strip()

    @property
    def ESIGN_WEBHOOK_SECRET(self) -> str:
        """Connect HMAC secret (DocuSign) or shared HMAC secret (stub / PHI header)."""
        return os.getenv("PHI_DPS_ESIGN_WEBHOOK_SECRET", "").strip()

    @property
    def ESIGN_ACCOUNT_ID(self) -> str:
        return os.getenv("PHI_DPS_ESIGN_ACCOUNT_ID", "").strip()

    @property
    def ESIGN_TEMPLATE_ID(self) -> str:
        return os.getenv("PHI_DPS_ESIGN_TEMPLATE_ID", "").strip()

    @property
    def ESIGN_RETURN_URL(self) -> str:
        """DocuSign embedded signing returnUrl (customer browser redirect after session)."""
        return (os.getenv("PHI_DPS_ESIGN_RETURN_URL") or "").strip()

    # warn_only | require_formal_acceptance_for_amendment | require_formal_acceptance_for_activation |
    # require_provider_esign_for_activation | require_provider_esign_for_amendment_and_activation
    @property
    def ACCEPTANCE_POLICY_MODE(self) -> str:
        return (os.getenv("PHI_DPS_ACCEPTANCE_POLICY_MODE", "warn_only") or "warn_only").strip().lower()

    @property
    def AUTO_CREATE_ACTIVATION_CONFIRMATION_ON_ACTIVATE(self) -> bool:
        """When true, successful amendment activation creates a pending activation confirmation row (§5.3)."""
        return os.getenv("PHI_DPS_AUTO_CREATE_ACTIVATION_CONFIRMATION_ON_ACTIVATE", "0") == "1"

    # One JSON line per HTTP request to logger phi_dps.access (§5.7); skips /health and /health/ready.
    LOG_JSON_ACCESS: bool = os.getenv("PHI_DPS_LOG_JSON_ACCESS", "0") == "1"


settings = Settings()

