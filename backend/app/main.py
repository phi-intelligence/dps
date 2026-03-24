from __future__ import annotations

import json
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.api.routes import api_router
from backend.app.webhooks.communication_webhook_routes import router as communication_webhook_router
from backend.app.webhooks.esign_webhook_routes import router as esign_webhook_router
from backend.app.core.config import settings
from backend.app.core.security import decode_access_token
from backend.app.db.base import Base
from backend.app.db.sqlite_migrations import migrate_sqlite_schema
from backend.app.db.session import SessionLocal, engine
from backend.app.modules.auth.service import ensure_default_admin
from backend.app.modules.audit.models import AuditLog  # noqa: F401
from backend.app.modules.audit.service import create_audit_log
from backend.app.modules.rollout.scheduler import start_rollout_scheduler_background
from backend.app.services.runtime_settings_service import warm_runtime_settings_cache

# Import models so SQLAlchemy knows about them before create_all.
from backend.app.modules.auth.models import Role, User  # noqa: F401
from backend.app.modules.crm.models import Customer, Lead  # noqa: F401
from backend.app.modules.quoting.models import Quote, QuoteItem  # noqa: F401
from backend.app.modules.dispatch.models import (  # noqa: F401
    Job,
    DispatchDecisionLog,
    JobEtaDelayNotice,
    JobEtaState,
    JobFormRequirement,
    JobFormSubmission,
    JobSignatureRequirement,
    JobSignatureSubmission,
    JobMediaRequirement,
    JobMediaSubmission,
    JobMediaUploadSession,
    JobPartsUsageRequirement,
    JobPartsUsageSubmission,
    JobPartUsageLine,
    JobPartsReconciliationApproval,
    JobActivityEvent,
)
from backend.app.modules.tracking.models import (  # noqa: F401
    EngineerLatestLocation,
    EngineerTelemetryEvent,
    JobGeofence,
    VehicleLatestLocation,
    VehicleTelemetryEvent,
    VehicleTelemetryPoint,
)
from backend.app.modules.time_tracking.models import Punch  # noqa: F401
from backend.app.modules.compliance.models import Certificate  # noqa: F401
from backend.app.modules.invoicing.models import Invoice  # noqa: F401
from backend.app.modules.costing.models import JobCostSnapshot, JobCostSnapshotLine, LabourRateProfile  # noqa: F401
from backend.app.modules.contracts.models import Contract  # noqa: F401
from backend.app.modules.contracts.proposal_acceptance_models import (  # noqa: F401
    ProposalAcceptanceRecord,
    ProposalAcceptanceSession,
)
from backend.app.modules.contracts.review_models import (  # noqa: F401
    ContractCommercialActionLog,
    ContractRepricingProposal,
    ContractRepricingProposalLine,
    ContractRepricingReview,
    ContractReview,
    ProposalCustomerResponse,
)
from backend.app.modules.contracts.amendment_models import ContractAmendment  # noqa: F401
from backend.app.modules.contracts.contract_version_models import (  # noqa: F401
    ContractActivationRun,
    ContractVersion,
)
from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation  # noqa: F401
from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication  # noqa: F401
from backend.app.modules.contracts.contract_customer_communication_delivery_models import (  # noqa: F401
    ContractCustomerCommunicationDelivery,
)
from backend.app.modules.contracts.communication_provider_event_models import (  # noqa: F401
    CommunicationProviderEvent,
    CommunicationRecipientSuppression,
)
from backend.app.modules.crm.customer_communication_preference_models import (  # noqa: F401
    CustomerCommunicationPreference,
)
from backend.app.modules.contracts.performance_models import ContractPerformanceSnapshot  # noqa: F401
from backend.app.modules.assets.models import Asset  # noqa: F401
from backend.app.modules.sites.models import Site  # noqa: F401
from backend.app.modules.sla.models import SlaPolicy  # noqa: F401
from backend.app.modules.ppm.models import PpmGenerationRecord, PpmSchedule  # noqa: F401
from backend.app.modules.portal.models import CustomerCommsEvent, PortalSiteAccess  # noqa: F401
from backend.app.modules.ops.models import (  # noqa: F401
    OperationalRecommendation,
    RecommendationActionDecision,
    RecommendationActionSuggestion,
    RecommendationOccurrenceEvent,
    RecommendationSuppression,
)
from backend.app.modules.competence.models import Qualification  # noqa: F401
from backend.app.modules.inventory.models import (  # noqa: F401
    InventoryLedgerEntry,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequest,
    StockBalance,
    StockItem,
    StockLocation,
    StockReservation,
    StockTransaction,
    StockTransfer,
    StockTransferLine,
)
from backend.app.modules.analytics.models import AnalyticsSnapshot  # noqa: F401
from backend.app.modules.rollout.models import (  # noqa: F401
    NotificationDelivery,
    NotificationWebhookEvent,
    RolloutAlert,
    PilotFeedback,
    PilotUser,
    RolloutPolicy,
    RolloutWave,
    UsageEvent,
)
from backend.app.modules.documents.models import DocumentAccessLog, StoredDocument  # noqa: F401
from backend.app.modules.equipment.models import (  # noqa: F401
    EquipmentCalibrationRecord,
    EquipmentInspectionRecord,
    EquipmentMovement,
    FieldEquipment,
    JobEquipmentRequirement,
)
from backend.app.modules.vehicles.models import (  # noqa: F401
    VehicleDefect,
    VehicleInspection,
    VehicleInspectionItem,
)
from backend.app.modules.approvals.models import ApprovalAuditLog, ApprovalRequest  # noqa: F401
from backend.app.modules.labour.models import HolidayCalendar, HolidayCalendarDay, LabourRuleSet  # noqa: F401
from backend.app.modules.automation.models import AutomationRun, InternalFollowUpTask  # noqa: F401
from backend.app.modules.system.break_glass_models import BreakGlassOverrideAudit  # noqa: F401
from backend.app.modules.system.recurring_system_job_models import (  # noqa: F401
    RecurringSystemJob,
    RecurringSystemJobRun,
)
from backend.app.modules.common.idempotency_models import ApiIdempotencyRecord  # noqa: F401
from backend.app.modules.auth.permission_models import PermissionGrantAuditLog, UserPermissionGrant  # noqa: F401
from backend.app.modules.auth.admin_settings_models import AdminSettingAuditLog, AdminSettingValue  # noqa: F401
from backend.app.modules.auth.org_access_models import (  # noqa: F401
    CustomerAccessGroup,
    CustomerAccessGroupMembership,
    CustomerGroupEntityAccess,
    GroupEntityAccess,
    GroupPermissionGrant,
    InternalAccessGroup,
    InternalAccessGroupMembership,
    OrgAccessAuditLog,
)


app = FastAPI(title="PHI-DPS", version="0.1.0")

_access_logger = logging.getLogger("phi_dps.access")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(communication_webhook_router)
app.include_router(esign_webhook_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "phi-dps-api"}


@app.get("/health/ready", response_model=None)
def health_ready() -> JSONResponse | dict[str, str]:
    """Liveness does not check dependencies; readiness includes a DB round-trip (§5.7)."""
    db: Session = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": str(e)[:300]},
        )
    finally:
        db.close()


@app.middleware("http")
async def security_and_audit_middleware(request: Request, call_next):
    response = await call_next(request)

    # Basic hardening headers (best-effort).
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=()")

    # Best-effort audit logging for write operations and portal actions.
    # Audit logging should never block the response.
    try:
        should_audit = request.method in {"POST", "PUT", "PATCH", "DELETE"} or request.url.path.startswith("/portal/")
        if should_audit:
            actor_user_id: str | None = None
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1]
                payload = decode_access_token(token)
                actor_user_id = payload.get("sub")

            db: Session = SessionLocal()
            try:
                create_audit_log(
                    db,
                    actor_user_id=actor_user_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    action=None,
                )
            finally:
                db.close()
    except Exception:
        pass

    return response


@app.middleware("http")
async def json_access_log_middleware(request: Request, call_next):
    if not settings.LOG_JSON_ACCESS:
        return await call_next(request)
    path = request.url.path
    if path in ("/health", "/health/ready"):
        return await call_next(request)
    t0 = time.perf_counter()
    response = await call_next(request)
    rec = {
        "event": "http_access",
        "method": request.method,
        "path": path,
        "status_code": response.status_code,
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
    }
    _access_logger.info(json.dumps(rec, separators=(",", ":")))
    return response


@app.on_event("startup")
def on_startup() -> None:
    # Schema bootstrap (§5.6): create_all + SQLite additive migrations are idempotent — safe if the process restarts.
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema(engine)

    # Dev bootstrap makes first login possible without manual SQL.
    if os.getenv("PHI_DPS_DEV_BOOTSTRAP", "1") == "1":
        db: Session = SessionLocal()
        try:
            ensure_default_admin(db)
            from backend.app.modules.inventory.ledger_service import (
                ensure_default_inventory_locations,
                sync_legacy_stock_items_to_default_warehouse,
            )

            ensure_default_inventory_locations(db)
            sync_legacy_stock_items_to_default_warehouse(db)
            from backend.app.modules.costing.labour_bootstrap import ensure_default_labour_profile

            ensure_default_labour_profile(db)
        finally:
            db.close()

    # Phase 5.4: lightweight internal rollout scheduler (dev/staging only, env-gated).
    start_rollout_scheduler_background()

    # Phase 5.20: warm runtime settings cache for fast/effective-prints (§ enterprise settings).
    try:
        db: Session = SessionLocal()
        try:
            warm_runtime_settings_cache(db)
        finally:
            db.close()
    except Exception:
        # Best-effort: should never block startup.
        pass

