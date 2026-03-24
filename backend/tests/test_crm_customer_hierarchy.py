"""§5.12 — optional parent customer link on CRM records."""
from __future__ import annotations

import uuid

import pytest

from backend.app.modules.crm.models import Customer
from backend.app.modules.crm.schemas import CustomerPatchIn
from backend.app.modules.crm.service import patch_customer


@pytest.fixture(scope="session", autouse=True)
def _db_ready():
    from backend.app.db.base import Base
    from backend.app.db.session import engine
    from backend.app.db.sqlite_migrations import migrate_sqlite_schema

    import backend.app.main  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema(engine)
    yield


def test_patch_customer_parent_round_trip():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        p = Customer(id=str(uuid.uuid4()), name="Parent Org", email=f"parent_{uuid.uuid4().hex[:8]}@t.com")
        c = Customer(id=str(uuid.uuid4()), name="Subsidiary", email=f"sub_{uuid.uuid4().hex[:8]}@t.com")
        db.add_all([p, c])
        db.commit()
        out = patch_customer(db, customer_id=c.id, patch=CustomerPatchIn(parent_customer_id=p.id))
        assert out.parent_customer_id == p.id
        out2 = patch_customer(db, customer_id=c.id, patch=CustomerPatchIn(parent_customer_id=None))
        assert out2.parent_customer_id is None
    finally:
        db.close()
