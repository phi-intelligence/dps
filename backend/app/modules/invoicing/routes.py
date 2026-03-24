from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.services.authorization_policy import CAN_HOLD_INVOICE, CAN_RELEASE_INVOICE
from backend.app.services.authorization_service import require_permission_http
from backend.app.modules.documents.persist import regenerate_invoice_document
from backend.app.modules.documents.schemas import StoredDocumentOut
from backend.app.modules.documents.service import stored_document_out_from_row
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.invoicing.schemas import (
    InvoiceFinanceReviewNoteIn,
    InvoiceGenerateIn,
    InvoiceHoldIn,
    InvoiceOut,
    InvoiceReleaseHoldIn,
)
from backend.app.modules.invoicing.service import (
    clear_invoice_finance_review,
    finance_operations_dashboard,
    generate_invoice,
    hold_invoice,
    invoice_export_rows,
    invoice_reconciliation_summary,
    list_invoices,
    mark_invoice_finance_reviewed,
    pay_invoice,
    release_invoice_from_hold,
)


router = APIRouter(prefix="/invoicing", tags=["invoicing"])


@router.post("/invoices/generate", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def generate_invoice_endpoint(
    payload: InvoiceGenerateIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Finance")),
) -> InvoiceOut:
    try:
        return generate_invoice(db, job_id=payload.job_id, acting_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices_endpoint(
    job_id: str | None = Query(default=None),
    status: str | None = Query(default=None, description="Filter: unpaid | held | paid"),
    finance_reviewed: bool | None = Query(default=None, description="True = reviewed only; False = not reviewed"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Finance")),
) -> list[InvoiceOut]:
    return list_invoices(
        db,
        job_id=job_id,
        status=status,
        finance_reviewed=finance_reviewed,
        limit=limit,
        offset=offset,
    )


@router.get("/dashboard/reconciliation-summary")
def invoicing_reconciliation_summary_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Finance")),
) -> dict:
    return invoice_reconciliation_summary(db)


@router.get("/invoices/export-rows")
def invoicing_invoice_export_rows_endpoint(
    limit: int = Query(default=500, le=2000),
    status: str | None = Query(default=None, description="Optional status filter"),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Finance")),
) -> list[dict]:
    return invoice_export_rows(db, limit=limit, status=status)


@router.post(
    "/invoices/{invoice_id}/regenerate-pdf",
    response_model=StoredDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def regenerate_invoice_pdf_endpoint(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Finance")),
) -> StoredDocumentOut:
    if not db.get(Invoice, invoice_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        row = regenerate_invoice_document(
            db, invoice_id=invoice_id, uploaded_by_user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return stored_document_out_from_row(row)


@router.post("/invoices/{invoice_id}/hold", response_model=InvoiceOut)
def hold_invoice_endpoint(
    invoice_id: str,
    payload: InvoiceHoldIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Finance", "Ops_Manager")),
) -> InvoiceOut:
    require_permission_http(current_user, CAN_HOLD_INVOICE, db=db)
    if not db.get(Invoice, invoice_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        return hold_invoice(
            db, invoice_id=invoice_id, note=payload.note, acting_user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/invoices/{invoice_id}/release-hold", response_model=InvoiceOut)
def release_invoice_hold_endpoint(
    invoice_id: str,
    payload: InvoiceReleaseHoldIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Finance", "Ops_Manager")),
) -> InvoiceOut:
    require_permission_http(current_user, CAN_RELEASE_INVOICE, db=db)
    if not db.get(Invoice, invoice_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        return release_invoice_from_hold(
            db, invoice_id=invoice_id, note=payload.note, acting_user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/invoices/{invoice_id}/pay", response_model=InvoiceOut)
def pay_invoice_endpoint(
    invoice_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Finance")),
) -> InvoiceOut:
    try:
        return pay_invoice(db, invoice_id=invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/dashboard/finance-queue")
def finance_queue_dashboard_endpoint(
    limit_queue: int = Query(default=100, le=300),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Finance")),
) -> dict:
    return finance_operations_dashboard(db, limit_queue=limit_queue)


@router.post("/invoices/{invoice_id}/finance-review", response_model=InvoiceOut)
def mark_invoice_finance_review_endpoint(
    invoice_id: str,
    payload: InvoiceFinanceReviewNoteIn = InvoiceFinanceReviewNoteIn(),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Finance")),
) -> InvoiceOut:
    if not db.get(Invoice, invoice_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        return mark_invoice_finance_reviewed(
            db,
            invoice_id=invoice_id,
            acting_user_id=current_user.id,
            note=payload.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/invoices/{invoice_id}/clear-finance-review", response_model=InvoiceOut)
def clear_invoice_finance_review_endpoint(
    invoice_id: str,
    payload: InvoiceFinanceReviewNoteIn = InvoiceFinanceReviewNoteIn(),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Finance")),
) -> InvoiceOut:
    if not db.get(Invoice, invoice_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        return clear_invoice_finance_review(
            db, invoice_id=invoice_id, note=payload.note
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

