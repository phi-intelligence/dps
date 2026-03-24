from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.assets.models import Asset, MaintenanceSchedule
from backend.app.modules.compliance.models import Certificate
from backend.app.modules.dispatch.models import Job


def build_site_history(db: Session, *, site_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for j in db.query(Job).filter(Job.site_id == site_id).order_by(Job.created_at.desc()).limit(200).all():
        rows.append(
            {
                "kind": "job",
                "id": j.id,
                "at": j.created_at.isoformat(),
                "summary": f"Job {j.status} ({j.work_type or 'reactive'})",
                "status": j.status,
                "work_type": j.work_type,
                "contract_id": j.contract_id,
            }
        )

    for c in db.query(Certificate).filter(Certificate.site_id == site_id).order_by(Certificate.created_at.desc()).all():
        rows.append(
            {
                "kind": "certificate",
                "id": c.id,
                "at": c.created_at.isoformat(),
                "summary": f"Certificate {c.certificate_type} ({c.status})",
                "job_id": c.job_id,
            }
        )

    rows.sort(key=lambda r: r["at"], reverse=True)
    return rows


def build_asset_history(db: Session, *, asset_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    asset = db.get(Asset, asset_id)
    if asset and asset.notes:
        rows.append(
            {
                "kind": "note",
                "id": asset.id,
                "at": asset.created_at.isoformat(),
                "summary": asset.notes[:500],
            }
        )

    for j in db.query(Job).filter(Job.asset_id == asset_id).order_by(Job.created_at.desc()).limit(200).all():
        rows.append(
            {
                "kind": "job",
                "id": j.id,
                "at": j.created_at.isoformat(),
                "summary": f"Job {j.status} ({j.work_type or 'reactive'})",
                "status": j.status,
                "work_type": j.work_type,
            }
        )

    for c in db.query(Certificate).filter(Certificate.asset_id == asset_id).order_by(Certificate.created_at.desc()).all():
        rows.append(
            {
                "kind": "certificate",
                "id": c.id,
                "at": c.created_at.isoformat(),
                "summary": f"Certificate {c.certificate_type} ({c.status})",
                "job_id": c.job_id,
            }
        )

    for s in (
        db.query(MaintenanceSchedule)
        .filter(MaintenanceSchedule.asset_id == asset_id)
        .order_by(MaintenanceSchedule.next_due_at.desc())
        .limit(50)
        .all()
    ):
        rows.append(
            {
                "kind": "maintenance_schedule",
                "id": s.id,
                "at": s.next_due_at.isoformat(),
                "summary": f"Maintenance schedule next due {s.next_due_at.date().isoformat()}",
            }
        )

    rows.sort(key=lambda r: r["at"], reverse=True)
    return rows
