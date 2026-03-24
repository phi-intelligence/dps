from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.sla.schemas import SlaPolicyCreateIn, SlaPolicyOut, SlaPolicyPatchIn
from backend.app.modules.sla.service import create_sla_policy, get_sla_policy, list_sla_policies, patch_sla_policy

router = APIRouter(prefix="/sla", tags=["sla"])


@router.post("/policies", response_model=SlaPolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: SlaPolicyCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> SlaPolicyOut:
    return create_sla_policy(db, payload=payload)


@router.get("/policies", response_model=list[SlaPolicyOut])
def list_policies(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[SlaPolicyOut]:
    return list_sla_policies(db, active_only=active_only)


@router.get("/policies/{policy_id}", response_model=SlaPolicyOut)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> SlaPolicyOut:
    p = get_sla_policy(db, policy_id=policy_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return p


@router.patch("/policies/{policy_id}", response_model=SlaPolicyOut)
def patch_policy(
    policy_id: str,
    payload: SlaPolicyPatchIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> SlaPolicyOut:
    try:
        return patch_sla_policy(db, policy_id=policy_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
