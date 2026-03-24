from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.time_tracking.schemas import (
    PayrollExportOut,
    PunchInOutIn,
    PunchOut,
    TimesheetApprovalIn,
    TimesheetApprovalOut,
    TimesheetOut,
)
from backend.app.modules.time_tracking.service import (
    approve_timesheet,
    export_payroll_for_date,
    get_timesheet,
    punch_in,
    punch_out,
)
from backend.app.services.idempotency_service import (
    canonical_request_hash,
    lookup_cached_json,
    save_idempotent_success,
)


router = APIRouter(prefix="/time", tags=["time"])


@router.post("/punch/in", response_model=PunchOut)
def punch_in_endpoint(
    payload: PunchInOutIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> PunchOut:
    scope = "POST:/time/punch/in"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return PunchOut.model_validate(cached[1])
    try:
        punch = punch_in(db, user_id=current_user.id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    out = PunchOut.model_validate(punch)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
    )
    return out


@router.post("/punch/out", response_model=PunchOut)
def punch_out_endpoint(
    payload: PunchInOutIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> PunchOut:
    scope = "POST:/time/punch/out"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return PunchOut.model_validate(cached[1])
    try:
        punch = punch_out(db, user_id=current_user.id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    out = PunchOut.model_validate(punch)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
    )
    return out


@router.get("/timesheets", response_model=TimesheetOut)
def timesheet_endpoint(
    date: str = Query(..., description="YYYY-MM-DD (UTC)"),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
) -> TimesheetOut:
    try:
        return get_timesheet(db, user_id=current_user.id, date_str=date)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/timesheets/approve", response_model=TimesheetApprovalOut)
def approve_timesheet_endpoint(
    payload: TimesheetApprovalIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> TimesheetApprovalOut:
    try:
        return approve_timesheet(
            db,
            user_id=payload.user_id,
            date_str=payload.date_str,
            approved_by_user_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/payroll/export", response_model=PayrollExportOut)
def export_payroll_endpoint(
    payload: TimesheetApprovalIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> PayrollExportOut:
    # payload.user_id is ignored; kept to reuse a stable body shape.
    return export_payroll_for_date(db, date_str=payload.date_str)

