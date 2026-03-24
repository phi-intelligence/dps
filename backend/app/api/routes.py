from fastapi import APIRouter

from backend.app.modules.auth.routes import router as auth_router
from backend.app.modules.crm.communication_preference_routes import router as customer_comm_prefs_router
from backend.app.modules.crm.routes import router as crm_router
from backend.app.modules.quoting.routes import router as quoting_router
from backend.app.modules.dispatch.routes import router as dispatch_router
from backend.app.modules.dispatch.dispatch_intelligence_routes import router as dispatch_intelligence_router
from backend.app.modules.dispatch.dispatch_tracking_routes import router as dispatch_tracking_router
from backend.app.modules.tracking.routes import router as tracking_router
from backend.app.modules.time_tracking.routes import router as time_router
from backend.app.modules.compliance.routes import router as compliance_router
from backend.app.modules.invoicing.routes import router as invoicing_router
from backend.app.modules.portal.routes import router as portal_router
from backend.app.modules.assets.routes import router as assets_router
from backend.app.modules.competence.routes import router as competence_router
from backend.app.modules.inventory.routes import router as inventory_router
from backend.app.modules.analytics.routes import router as analytics_router
from backend.app.modules.integrations.routes import router as integrations_router
from backend.app.modules.rollout.routes import router as rollout_router
from backend.app.modules.system.routes import router as system_router
from backend.app.modules.contracts.routes import router as contracts_router
from backend.app.modules.sites.routes import router as sites_router
from backend.app.modules.sla.routes import router as sla_router
from backend.app.modules.ppm.routes import router as ppm_router
from backend.app.modules.ops.routes import router as ops_router
from backend.app.modules.documents.routes import router as documents_router
from backend.app.modules.equipment.routes import router as equipment_router
from backend.app.modules.vehicles.routes import router as vehicles_router
from backend.app.modules.approvals.routes import router as approvals_router
from backend.app.modules.labour.routes import router as labour_router
from backend.app.modules.ai.drafting_routes import router as ai_drafting_router
from backend.app.modules.automation.routes import automation_router, tasks_router
from backend.app.modules.auth.admin_routes import router as admin_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(crm_router)
api_router.include_router(customer_comm_prefs_router)
api_router.include_router(quoting_router)
api_router.include_router(dispatch_router)
api_router.include_router(dispatch_intelligence_router)
api_router.include_router(dispatch_tracking_router)
api_router.include_router(tracking_router)
api_router.include_router(time_router)
api_router.include_router(compliance_router)
api_router.include_router(invoicing_router)
api_router.include_router(portal_router)
api_router.include_router(assets_router)
api_router.include_router(competence_router)
api_router.include_router(inventory_router)
api_router.include_router(analytics_router)
api_router.include_router(integrations_router)
api_router.include_router(rollout_router)
api_router.include_router(system_router)
api_router.include_router(sites_router)
api_router.include_router(sla_router)
api_router.include_router(ppm_router)
api_router.include_router(contracts_router)
api_router.include_router(ops_router)
api_router.include_router(documents_router)
api_router.include_router(equipment_router)
api_router.include_router(vehicles_router)
api_router.include_router(approvals_router)
api_router.include_router(labour_router)
api_router.include_router(ai_drafting_router)
api_router.include_router(automation_router)
api_router.include_router(tasks_router)

