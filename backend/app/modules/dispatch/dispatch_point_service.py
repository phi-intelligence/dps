from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.modules.dispatch.models import Job
from backend.app.modules.sites.models import Site
from backend.app.modules.tracking.service import get_job_geofence


@dataclass(frozen=True)
class DispatchPoint:
    latitude: float
    longitude: float
    source: str  # site_coordinates | geofence_center | geocoded_address


def resolve_job_dispatch_point(db: Session, *, job_id: str) -> DispatchPoint:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    if job.site_latitude is not None and job.site_longitude is not None:
        return DispatchPoint(latitude=float(job.site_latitude), longitude=float(job.site_longitude), source="site_coordinates")

    if job.site_id:
        site = db.get(Site, job.site_id)
        if site and site.latitude is not None and site.longitude is not None:
            return DispatchPoint(
                latitude=float(site.latitude),
                longitude=float(site.longitude),
                source="site_master_record",
            )

    geofence = get_job_geofence(db, job_id=job_id)
    if geofence:
        return DispatchPoint(
            latitude=float(geofence.latitude),
            longitude=float(geofence.longitude),
            source="geofence_center",
        )

    if job.address_geocoded_latitude is not None and job.address_geocoded_longitude is not None:
        return DispatchPoint(
            latitude=float(job.address_geocoded_latitude),
            longitude=float(job.address_geocoded_longitude),
            source="geocoded_address",
        )

    raise ValueError(
        "Cannot resolve dispatch coordinates for this job. "
        "Set site_latitude/site_longitude, configure a job geofence, or provide address_geocoded_latitude/longitude."
    )
