from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.quoting.schemas import QuoteAcceptOut, QuoteCreateIn, QuoteOut
from backend.app.modules.quoting.service import accept_quote, create_quote, list_quotes
from backend.app.modules.quoting.models import Quote


router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("", response_model=QuoteOut, status_code=status.HTTP_201_CREATED)
def create_quote_endpoint(
    payload: QuoteCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> QuoteOut:
    return create_quote(db, payload=payload)


@router.get("", response_model=list[QuoteOut])
def list_quotes_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[QuoteOut]:
    return list_quotes(db, limit=limit, offset=offset)


@router.get("/{quote_id}", response_model=QuoteOut)
def get_quote_endpoint(
    quote_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> QuoteOut:
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return quote


@router.post("/{quote_id}/accept", response_model=QuoteAcceptOut)
def accept_quote_endpoint(
    quote_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> QuoteAcceptOut:
    try:
        quote = accept_quote(db, quote_id=quote_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return QuoteAcceptOut(quote=quote)

