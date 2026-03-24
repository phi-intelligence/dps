"""PDF generation, S3-compatible storage abstraction, regeneration, and portal retrieval."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest


def _token(client, username: str, password: str) -> str:
    r = client.post("/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def pdf_portal_customer():
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User
    from backend.app.modules.crm.models import Customer

    email = "pdf_portal_slice@example.com"
    password = "pdfportal"
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == email).first():
            role = db.query(Role).filter(Role.name == "Client").one()
            db.add(User(email=email, hashed_password=hash_password(password), roles=[role]))
            db.commit()
        if not db.query(Customer).filter(Customer.email == email).first():
            db.add(Customer(name="PDF Portal Customer", email=email))
            db.commit()
        cust = db.query(Customer).filter(Customer.email == email).one()
        return {"email": email, "password": password, "customer_id": cust.id}
    finally:
        db.close()


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


def test_s3_compatible_storage_uses_put_object(monkeypatch):
    from backend.app.core import config
    from backend.app.services import document_storage_service as dss

    mock_client = MagicMock()
    monkeypatch.setattr(config.settings, "PHI_DPS_DOCUMENT_STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(config.settings, "PHI_DPS_S3_BUCKET", "unit-test-bucket")
    monkeypatch.setattr(dss, "_build_boto3_s3_client", lambda: mock_client)

    key = dss.build_storage_key(document_type="invoice", document_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890", filename_safe="x.pdf")
    dss.save_binary(storage_key=key, data=b"hello-pdf")
    mock_client.put_object.assert_called_once()
    call_kw = mock_client.put_object.call_args.kwargs
    assert call_kw["Bucket"] == "unit-test-bucket"
    assert call_kw["Body"] == b"hello-pdf"

    mock_client.head_object.side_effect = _client_error_404()
    assert dss.document_exists(storage_key=key) is False
    mock_client.head_object.side_effect = None
    mock_client.head_object.return_value = {}
    assert dss.document_exists(storage_key=key) is True

    mock_client.generate_presigned_url.return_value = "https://signed.example/presigned"
    backend = dss.S3CompatibleStorage(bucket="b", prefix="pfx", client=mock_client)
    assert "signed" in backend.get_presigned_download_url(storage_key="k/x.pdf")


def _client_error_404():
    from botocore.exceptions import ClientError

    return ClientError({"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}}, "HeadObject")


def test_regenerate_certificate_creates_second_stored_document_row(client, pdf_portal_customer):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": pdf_portal_customer["customer_id"], "address": "Regen cert job"},
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

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        n1 = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_certificate_id == cert_id)
            .count()
        )
        first_id = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_certificate_id == cert_id)
            .order_by(StoredDocument.created_at.asc())
            .first()
            .id
        )
    finally:
        db.close()
    assert n1 == 1

    reg = client.post(f"/compliance/certificates/{cert_id}/regenerate-pdf", headers=_h(admin))
    assert reg.status_code == 201, reg.text
    body = reg.json()
    assert body["related_certificate_id"] == cert_id
    assert body["checksum_sha256"]
    meta = json.loads(body["metadata_json"])
    assert meta.get("regenerated") is True
    assert meta.get("prior_stored_document_id") == first_id

    db = SessionLocal()
    try:
        n2 = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_certificate_id == cert_id)
            .count()
        )
        latest = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_certificate_id == cert_id)
            .order_by(StoredDocument.created_at.desc())
            .first()
        )
    finally:
        db.close()
    assert n2 == 2
    assert latest.id != first_id


def test_generated_invoice_pdf_contains_business_markers(client, pdf_portal_customer):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": pdf_portal_customer["customer_id"], "address": "PDF marker job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    inv_r = client.post("/invoicing/invoices/generate", headers=_h(admin), json={"job_id": job_id})
    assert inv_r.status_code == 201, inv_r.text
    inv_id = inv_r.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument
    from backend.app.services import document_storage_service as doc_store

    db = SessionLocal()
    try:
        row = db.query(StoredDocument).filter(StoredDocument.related_invoice_id == inv_id).one()
        raw = doc_store.stream_document(storage_key=row.storage_key).read()
        meta = json.loads(row.metadata_json or "{}")
    finally:
        db.close()

    assert raw.startswith(b"%PDF")
    assert meta.get("renderer") == "invoice_pdf_reportlab_v1"
    tag = f"phi-dps-invoice-docid-{inv_id}".encode()
    assert tag in raw
    assert b"Labour" in raw or b"labour" in raw.lower()


def test_generated_certificate_pdf_contains_business_markers(client, pdf_portal_customer):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": pdf_portal_customer["customer_id"], "address": "Cert PDF job"},
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
    from backend.app.services import document_storage_service as doc_store

    db = SessionLocal()
    try:
        row = db.query(StoredDocument).filter(StoredDocument.related_certificate_id == cert_id).one()
        raw = doc_store.stream_document(storage_key=row.storage_key).read()
        meta = json.loads(row.metadata_json or "{}")
    finally:
        db.close()

    assert raw.startswith(b"%PDF")
    assert meta.get("renderer") == "certificate_pdf_reportlab_v1"
    assert f"phi-dps-certificate-docid-{cert_id}".encode() in raw
    assert b"gas" in raw.lower()


def test_regenerate_invoice_creates_second_stored_document_row(client, pdf_portal_customer):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": pdf_portal_customer["customer_id"], "address": "Regen inv job"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    inv_r = client.post("/invoicing/invoices/generate", headers=_h(admin), json={"job_id": job_id})
    inv_id = inv_r.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        first_id = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_invoice_id == inv_id)
            .order_by(StoredDocument.created_at.asc())
            .first()
            .id
        )
    finally:
        db.close()

    reg = client.post(f"/invoicing/invoices/{inv_id}/regenerate-pdf", headers=_h(admin))
    assert reg.status_code == 201, reg.text
    meta = json.loads(reg.json()["metadata_json"])
    assert meta.get("prior_stored_document_id") == first_id

    db = SessionLocal()
    try:
        n = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_invoice_id == inv_id)
            .count()
        )
    finally:
        db.close()
    assert n == 2


def test_portal_certificate_download_returns_generated_pdf_bytes(client, pdf_portal_customer):
    admin = _token(client, "admin@example.com", "admin")
    ctok = _token(client, pdf_portal_customer["email"], pdf_portal_customer["password"])
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": pdf_portal_customer["customer_id"], "address": "Portal cert dl"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    cert_r = client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    cert_id = cert_r.json()["id"]
    dl = client.get(f"/portal/me/certificates/{cert_id}/download", headers=_h(ctok))
    assert dl.status_code == 200, dl.text
    assert dl.content.startswith(b"%PDF")
    assert f"phi-dps-certificate-docid-{cert_id}".encode() in dl.content


def test_portal_invoice_download_returns_latest_pdf_bytes(client, pdf_portal_customer):
    admin = _token(client, "admin@example.com", "admin")
    ctok = _token(client, pdf_portal_customer["email"], pdf_portal_customer["password"])
    cid = pdf_portal_customer["customer_id"]

    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": cid, "address": "Portal invoice dl"},
    )
    job_id = job_r.json()["id"]
    _complete_job(job_id)
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    inv_r = client.post("/invoicing/invoices/generate", headers=_h(admin), json={"job_id": job_id})
    inv_id = inv_r.json()["id"]

    client.post(f"/invoicing/invoices/{inv_id}/regenerate-pdf", headers=_h(admin))

    dl = client.get(f"/portal/me/invoices/{inv_id}/download", headers=_h(ctok))
    assert dl.status_code == 200, dl.text
    assert dl.content.startswith(b"%PDF")
    from backend.app.db.session import SessionLocal
    from backend.app.modules.documents.models import StoredDocument

    db = SessionLocal()
    try:
        latest = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_invoice_id == inv_id)
            .order_by(StoredDocument.created_at.desc())
            .first()
        )
        from backend.app.services import document_storage_service as doc_store

        expected = doc_store.stream_document(storage_key=latest.storage_key).read()
    finally:
        db.close()
    assert dl.content == expected
