from __future__ import annotations

import uuid

import pytest


def _token(client, username: str, password: str) -> str:
    r = client.post("/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def doc_slice_portal():
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User
    from backend.app.modules.crm.models import Customer

    email = "doc_slice_portal@example.com"
    password = "docslice"
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == email).first():
            role = db.query(Role).filter(Role.name == "Client").one()
            db.add(User(email=email, hashed_password=hash_password(password), roles=[role]))
            db.commit()
        if not db.query(Customer).filter(Customer.email == email).first():
            db.add(Customer(name="Doc Slice Portal", email=email))
            db.commit()
        cust = db.query(Customer).filter(Customer.email == email).one()
        return {"email": email, "password": password, "customer_id": cust.id}
    finally:
        db.close()


@pytest.fixture
def doc_slice_customer_id(doc_slice_portal):
    return doc_slice_portal["customer_id"]


def _complete_job(job_id: str) -> None:
    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.commit()
    finally:
        db.close()


def test_generated_certificate_and_invoice_create_stored_document_rows(client, doc_slice_customer_id):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": doc_slice_customer_id, "address": "Binary persistence job"},
    )
    assert job_r.status_code == 201, job_r.text
    job_id = job_r.json()["id"]
    _complete_job(job_id)

    cert_r = client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    assert cert_r.status_code == 201, cert_r.text
    cert_id = cert_r.json()["id"]

    inv_r = client.post(
        "/invoicing/invoices/generate",
        headers=_h(admin),
        json={"job_id": job_id},
    )
    assert inv_r.status_code == 201, inv_r.text
    inv_id = inv_r.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        cdoc = db.query(StoredDocument).filter(StoredDocument.related_certificate_id == cert_id).one()
        assert cdoc.document_type == "certificate"
        assert cdoc.storage_key
        assert cdoc.checksum_sha256
        assert cdoc.size_bytes > 0
        idoc = db.query(StoredDocument).filter(StoredDocument.related_invoice_id == inv_id).one()
        assert idoc.document_type == "invoice"
        assert idoc.related_job_id == job_id
    finally:
        db.close()


def test_admin_can_request_secure_download_for_internal_document(client, doc_slice_customer_id):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": doc_slice_customer_id, "address": "Admin dl job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    cert_r = client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    cert_id = cert_r.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        doc = db.query(StoredDocument).filter(StoredDocument.related_certificate_id == cert_id).one()
        doc_id = doc.id
    finally:
        db.close()

    link_r = client.post(f"/documents/{doc_id}/download-link", headers=_h(admin), json={})
    assert link_r.status_code == 200, link_r.text
    url = link_r.json()["download_url"]
    assert url.startswith("/documents/download?token=")
    token = url.split("token=", 1)[1]
    dl = client.get(f"/documents/download?token={token}")
    assert dl.status_code == 200, dl.text
    assert dl.headers.get("content-type", "").startswith("application/pdf")
    assert len(dl.content) > 100


def test_customer_can_download_authorized_customer_safe_document(client, doc_slice_portal, doc_slice_customer_id):
    admin = _token(client, "admin@example.com", "admin")
    ctok = _token(client, doc_slice_portal["email"], doc_slice_portal["password"])
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": doc_slice_customer_id, "address": "Portal dl job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        doc = db.query(StoredDocument).filter(StoredDocument.related_job_id == job_id).first()
        assert doc
        doc_id = doc.id
    finally:
        db.close()

    meta = client.get(f"/portal/me/documents/{doc_id}", headers=_h(ctok))
    assert meta.status_code == 200, meta.text
    assert meta.json()["downloadable"] is True

    dl = client.get(f"/portal/me/documents/{doc_id}/download", headers=_h(ctok))
    assert dl.status_code == 200, dl.text
    assert dl.headers.get("content-type", "").startswith("application/pdf")


def test_unauthorized_customer_cannot_access_another_customers_document(client, doc_slice_portal, doc_slice_customer_id):
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User
    from backend.app.modules.crm.models import Customer

    admin = _token(client, "admin@example.com", "admin")
    other_email = f"other-doc-{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        oc = Customer(name="Other Doc Customer", email=other_email)
        db.add(oc)
        db.commit()
        db.refresh(oc)
        oid = oc.id
        role = db.query(Role).filter(Role.name == "Client").one()
        db.add(User(email=other_email, hashed_password=hash_password("secret"), roles=[role]))
        db.commit()
    finally:
        db.close()

    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": oid, "address": "Other customer job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )

    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        doc = db.query(StoredDocument).filter(StoredDocument.related_job_id == job_id).one()
        doc_id = doc.id
    finally:
        db.close()

    victim_tok = _token(client, doc_slice_portal["email"], doc_slice_portal["password"])
    assert client.get(f"/portal/me/documents/{doc_id}", headers=_h(victim_tok)).status_code == 404
    assert client.get(f"/portal/me/documents/{doc_id}/download", headers=_h(victim_tok)).status_code == 404


def test_expired_signed_token_cannot_be_used(client, doc_slice_customer_id):
    from backend.app.modules.documents.download_token import create_document_download_token

    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": doc_slice_customer_id, "address": "Expiry job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        doc = db.query(StoredDocument).filter(StoredDocument.related_job_id == job_id).one()
        doc_id = doc.id
    finally:
        db.close()

    tok = create_document_download_token(
        document_id=doc_id,
        context="internal",
        customer_id=None,
        ttl_seconds=-120,
    )
    r = client.get(f"/documents/download?token={tok}")
    assert r.status_code == 401


def test_download_attempts_create_audit_log_rows(client, doc_slice_customer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import DocumentAccessLog, StoredDocument

    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": doc_slice_customer_id, "address": "Audit job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )

    db = SessionLocal()
    try:
        doc = db.query(StoredDocument).filter(StoredDocument.related_job_id == job_id).one()
        doc_id = doc.id
        before = db.query(DocumentAccessLog).filter(DocumentAccessLog.document_id == doc_id).count()
    finally:
        db.close()

    link_r = client.post(f"/documents/{doc_id}/download-link", headers=_h(admin), json={})
    assert link_r.status_code == 200, link_r.text
    token = link_r.json()["download_url"].split("token=", 1)[1]
    client.get(f"/documents/download?token={token}")

    db = SessionLocal()
    try:
        after = db.query(DocumentAccessLog).filter(DocumentAccessLog.document_id == doc_id).count()
        assert after > before
        types = {r.access_type for r in db.query(DocumentAccessLog).filter(DocumentAccessLog.document_id == doc_id).all()}
        assert "download_link" in types
        assert "binary_download" in types
    finally:
        db.close()


def test_internal_only_document_hidden_from_portal_list(client, doc_slice_customer_id, doc_slice_portal):
    admin = _token(client, "admin@example.com", "admin")
    ctok = _token(client, doc_slice_portal["email"], doc_slice_portal["password"])
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": doc_slice_customer_id, "address": "Internal only list"},
    )
    job_id = job_r.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument
    from backend.app.services import document_storage_service as doc_store

    key = doc_store.build_storage_key(document_type="report", document_id=str(uuid.uuid4()), filename_safe="x.pdf")
    data = b"%PDF-1.4 internal only test"
    doc_store.save_binary(storage_key=key, data=data)
    db = SessionLocal()
    try:
        row = StoredDocument(
            document_type="report",
            filename="internal.pdf",
            content_type="application/pdf",
            size_bytes=len(data),
            storage_key=key,
            storage_provider=doc_store.get_storage_provider_name(),
            checksum_sha256=doc_store.sha256_hex(data),
            related_job_id=job_id,
            source_type="uploaded",
            visibility_scope="internal_only",
            status="ready",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        sid = row.id
    finally:
        db.close()

    lst = client.get("/portal/me/documents", headers=_h(ctok))
    assert lst.status_code == 200, lst.text
    ids = {x.get("id") for x in lst.json()}
    assert sid not in ids


def test_internal_metadata_listing_returns_related_entity_context(client, doc_slice_customer_id):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": doc_slice_customer_id, "address": "Filter list job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    cert_r = client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    assert cert_r.status_code == 201, cert_r.text
    inv_r = client.post(
        "/invoicing/invoices/generate",
        headers=_h(admin),
        json={"job_id": job_id},
    )
    assert inv_r.status_code == 201, inv_r.text
    inv_id = inv_r.json()["id"]

    r = client.get(f"/documents?related_job_id={job_id}", headers=_h(admin))
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list) and len(body) >= 1
    inv_row = next((x for x in body if x.get("related_invoice_id") == inv_id), None)
    assert inv_row is not None
    assert inv_row["related_job_id"] == job_id
    assert inv_row["document_type"] == "invoice"
