from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.competence.schemas import QualificationCreateIn, QualificationOut
from backend.app.modules.competence.service import add_qualification, list_qualifications_for_engineer


router = APIRouter(prefix="/competence", tags=["competence"])


@router.post("/qualifications", response_model=QualificationOut, status_code=status.HTTP_201_CREATED)
def add_qualification_endpoint(
    payload: QualificationCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> QualificationOut:
    return add_qualification(db, payload=payload)


@router.get("/qualifications", response_model=list[QualificationOut])
def list_qualifications_endpoint(
    engineer_user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[QualificationOut]:
    return list_qualifications_for_engineer(db, engineer_user_id=engineer_user_id, limit=limit, offset=offset)

