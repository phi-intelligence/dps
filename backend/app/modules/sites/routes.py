from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.auth.models import User
from backend.app.services import scoped_access_service as scoped_access
from backend.app.modules.assets.schemas import AssetOut
from backend.app.modules.assets.service import list_assets
from backend.app.modules.contracts.history_service import build_site_history
from backend.app.modules.contracts.operational_views import site_jobs_summary
from backend.app.modules.sites.schemas import SiteCreateIn, SiteOut, SitePatchIn
from backend.app.modules.sites.service import create_site, get_site, list_sites, patch_site

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site_endpoint(
    payload: SiteCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> SiteOut:
    try:
        return create_site(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[SiteOut])
def list_sites_endpoint(
    customer_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> list[SiteOut]:
    rows = list_sites(db, customer_id=customer_id, limit=limit, offset=offset)
    return scoped_access.filter_sites_for_internal_user(db, current_user, rows)


@router.get("/{site_id}/assets", response_model=list[AssetOut])
def list_site_assets_endpoint(
    site_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[AssetOut]:
    if not get_site(db, site_id=site_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return list_assets(db, site_id=site_id, limit=200, offset=0)


@router.get("/{site_id}/history")
def site_history_endpoint(
    site_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_site(db, site_id=site_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return {"site_id": site_id, "entries": build_site_history(db, site_id=site_id)}


@router.get("/{site_id}/jobs")
def site_jobs_endpoint(
    site_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_site(db, site_id=site_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site_jobs_summary(db, site_id=site_id)


@router.get("/{site_id}", response_model=SiteOut)
def get_site_endpoint(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> SiteOut:
    site = get_site(db, site_id=site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if not scoped_access.user_can_access_internal_entity(
        db, current_user, entity_type="site", entity_id=site_id, required_scope="view"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site


@router.patch("/{site_id}", response_model=SiteOut)
def patch_site_endpoint(
    site_id: str,
    payload: SitePatchIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> SiteOut:
    try:
        return patch_site(db, site_id=site_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
