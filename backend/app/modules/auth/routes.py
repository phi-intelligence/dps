from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.modules.auth.schemas import TokenOut, UserOut
from backend.app.modules.auth.service import authenticate_user, ensure_default_admin, issue_token_for_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenOut:
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = issue_token_for_user(user)
    return TokenOut(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)) -> UserOut:
    return current_user


@router.post("/dev/bootstrap")
def dev_bootstrap(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Dev helper: creates default roles + admin user.
    Remove/lock down in production.
    """

    ensure_default_admin(db)
    return {"status": "ok"}

