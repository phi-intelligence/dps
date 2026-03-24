"""
Best-effort SQLite column adds for dev DBs without Alembic.

Idempotent: each ALTER runs only when the target column is missing. Safe to invoke on
every API startup alongside ``Base.metadata.create_all`` (§5.6). Non-SQLite engines no-op.
"""
from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def migrate_sqlite_schema(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    insp = inspect(engine)
    with engine.begin() as conn:
        if insp.has_table("stock_reservations"):
            cols = {c["name"] for c in insp.get_columns("stock_reservations")}
            if "location_id" not in cols:
                conn.execute(text("ALTER TABLE stock_reservations ADD COLUMN location_id VARCHAR(36)"))
            if "stock_item_id" not in cols:
                conn.execute(text("ALTER TABLE stock_reservations ADD COLUMN stock_item_id VARCHAR(36)"))

        if insp.has_table("stock_items"):
            cols = {c["name"] for c in insp.get_columns("stock_items")}
            if "unit_of_measure" not in cols:
                conn.execute(text("ALTER TABLE stock_items ADD COLUMN unit_of_measure VARCHAR(16) DEFAULT 'ea'"))

        if insp.has_table("invoices"):
            cols = {c["name"] for c in insp.get_columns("invoices")}
            if "job_cost_snapshot_id" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN job_cost_snapshot_id VARCHAR(36)"))
            if "materials_actual_cost" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN materials_actual_cost FLOAT"))
            if "cost_basis_notes" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN cost_basis_notes TEXT"))
            if "finance_reviewed_at" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN finance_reviewed_at DATETIME"))
            if "finance_reviewed_by_user_id" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN finance_reviewed_by_user_id VARCHAR(36)"))

        if insp.has_table("jobs"):
            cols = {c["name"] for c in insp.get_columns("jobs")}
            if "site_latitude" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN site_latitude FLOAT"))
            if "site_longitude" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN site_longitude FLOAT"))
            if "address_geocoded_latitude" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN address_geocoded_latitude FLOAT"))
            if "address_geocoded_longitude" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN address_geocoded_longitude FLOAT"))
            if "material_policy" not in cols:
                conn.execute(
                    text("ALTER TABLE jobs ADD COLUMN material_policy VARCHAR(32) DEFAULT 'materials_optional'")
                )
            if "dispatch_priority" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN dispatch_priority INTEGER DEFAULT 0"))
            if "required_competencies_json" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN required_competencies_json TEXT DEFAULT '[]'"))
            if "contract_id" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN contract_id VARCHAR(36)"))
            if "site_id" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN site_id VARCHAR(36)"))
            if "asset_id" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN asset_id VARCHAR(36)"))
            if "ppm_schedule_id" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN ppm_schedule_id VARCHAR(36)"))
            if "work_type" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN work_type VARCHAR(32) DEFAULT 'reactive'"))
            if "sla_policy_id" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN sla_policy_id VARCHAR(36)"))
            if "sla_priority" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN sla_priority VARCHAR(32)"))
            if "asset_criticality" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN asset_criticality VARCHAR(32)"))
            if "covered_under_contract" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN covered_under_contract INTEGER DEFAULT 0"))
            if "compliance_required" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN compliance_required INTEGER DEFAULT 0"))
            if "acknowledged_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN acknowledged_at DATETIME"))
            if "dispatched_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN dispatched_at DATETIME"))
            if "en_route_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN en_route_at DATETIME"))
            if "on_site_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN on_site_at DATETIME"))
            if "resolved_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN resolved_at DATETIME"))
            if "on_my_way_sent_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN on_my_way_sent_at DATETIME"))
            if "customer_notified_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN customer_notified_at DATETIME"))
            if "tracking_link_token" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN tracking_link_token VARCHAR(64)"))
            if "manual_eta_minutes" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN manual_eta_minutes INTEGER"))
            if "manual_eta_set_at" not in cols:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN manual_eta_set_at DATETIME"))

        if insp.has_table("contracts"):
            cols = {c["name"] for c in insp.get_columns("contracts")}
            if "site_id" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN site_id VARCHAR(36)"))
            if "contract_code" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN contract_code VARCHAR(64) NOT NULL DEFAULT ''"))
            if "contract_type" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN contract_type VARCHAR(64) NOT NULL DEFAULT 'ppm_plus_reactive'"))
            if "status" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active'"))
            if "renewal_review_date" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN renewal_review_date DATETIME"))
            if "contract_value" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN contract_value FLOAT"))
            if "covered_assets_mode" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN covered_assets_mode VARCHAR(32) NOT NULL DEFAULT 'all_assets'"))
            if "covered_asset_ids_json" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN covered_asset_ids_json TEXT NOT NULL DEFAULT '[]'"))
            if "service_inclusions_json" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN service_inclusions_json TEXT NOT NULL DEFAULT '[]'"))
            if "exclusions_json" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN exclusions_json TEXT NOT NULL DEFAULT '[]'"))
            if "notes" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN notes TEXT"))
            if "default_sla_policy_id" not in cols:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN default_sla_policy_id VARCHAR(36)"))

        if insp.has_table("assets"):
            cols = {c["name"] for c in insp.get_columns("assets")}
            if "site_id" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN site_id VARCHAR(36)"))
            if "contract_id" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN contract_id VARCHAR(36)"))
            if "asset_code" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN asset_code VARCHAR(64) NOT NULL DEFAULT ''"))
            if "manufacturer" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN manufacturer VARCHAR(255)"))
            if "model" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN model VARCHAR(255)"))
            if "install_date" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN install_date DATETIME"))
            if "commissioning_date" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN commissioning_date DATETIME"))
            if "warranty_expiry" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN warranty_expiry DATETIME"))
            if "status" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'in_service'"))
            if "criticality" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN criticality VARCHAR(32) NOT NULL DEFAULT 'standard'"))
            if "service_interval_value" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN service_interval_value INTEGER"))
            if "service_interval_unit" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN service_interval_unit VARCHAR(16)"))
            if "last_service_date" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN last_service_date DATETIME"))
            if "next_service_date" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN next_service_date DATETIME"))
            if "notes" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN notes TEXT"))
            if "compliance_tags_json" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN compliance_tags_json TEXT NOT NULL DEFAULT '[]'"))
            if "required_competencies_json" not in cols:
                conn.execute(text("ALTER TABLE assets ADD COLUMN required_competencies_json TEXT NOT NULL DEFAULT '[]'"))

        if insp.has_table("certificates"):
            cols = {c["name"] for c in insp.get_columns("certificates")}
            if "site_id" not in cols:
                conn.execute(text("ALTER TABLE certificates ADD COLUMN site_id VARCHAR(36)"))
            if "asset_id" not in cols:
                conn.execute(text("ALTER TABLE certificates ADD COLUMN asset_id VARCHAR(36)"))
            if "contract_id" not in cols:
                conn.execute(text("ALTER TABLE certificates ADD COLUMN contract_id VARCHAR(36)"))

        if insp.has_table("customers"):
            cols = {c["name"] for c in insp.get_columns("customers")}
            if "portal_profile" not in cols:
                conn.execute(
                    text("ALTER TABLE customers ADD COLUMN portal_profile VARCHAR(32) NOT NULL DEFAULT 'residential'")
                )

        if not insp.has_table("portal_site_access"):
            conn.execute(
                text(
                    """
                    CREATE TABLE portal_site_access (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        customer_id VARCHAR(36) NOT NULL,
                        site_id VARCHAR(36) NOT NULL,
                        access_level VARCHAR(32) NOT NULL DEFAULT 'full_access',
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )

        if not insp.has_table("customer_comms_events"):
            conn.execute(
                text(
                    """
                    CREATE TABLE customer_comms_events (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        job_id VARCHAR(36) NOT NULL,
                        event_type VARCHAR(64) NOT NULL,
                        payload_json TEXT NOT NULL DEFAULT '{}',
                        delivery_status VARCHAR(16) NOT NULL DEFAULT 'logged',
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )

        if insp.has_table("users"):
            cols = {c["name"] for c in insp.get_columns("users")}
            if "assigned_vehicle_id" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN assigned_vehicle_id VARCHAR(64)"))

        if not insp.has_table("operational_recommendations"):
            conn.execute(
                text(
                    """
                    CREATE TABLE operational_recommendations (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        recommendation_type VARCHAR(64) NOT NULL,
                        category VARCHAR(64) NOT NULL,
                        severity VARCHAR(16) NOT NULL,
                        confidence VARCHAR(16) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        summary TEXT NOT NULL,
                        detail_json TEXT NOT NULL DEFAULT '{}',
                        entity_type VARCHAR(64) NOT NULL,
                        entity_id VARCHAR(64) NOT NULL,
                        related_job_id VARCHAR(36),
                        related_engineer_id VARCHAR(36),
                        related_site_id VARCHAR(36),
                        related_asset_id VARCHAR(36),
                        related_contract_id VARCHAR(36),
                        related_invoice_id VARCHAR(36),
                        status VARCHAR(16) NOT NULL DEFAULT 'open',
                        recommendation_key VARCHAR(255) NOT NULL,
                        source_rule_version VARCHAR(32) NOT NULL,
                        acknowledged_at DATETIME,
                        resolved_at DATETIME,
                        acknowledged_by_user_id VARCHAR(36),
                        resolution_notes TEXT,
                        closed_as VARCHAR(24),
                        suppressed_until DATETIME,
                        suppression_notes TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )

        if insp.has_table("operational_recommendations"):
            ocols = {c["name"] for c in insp.get_columns("operational_recommendations")}
            if "closed_as" not in ocols:
                conn.execute(text("ALTER TABLE operational_recommendations ADD COLUMN closed_as VARCHAR(24)"))
            if "suppressed_until" not in ocols:
                conn.execute(text("ALTER TABLE operational_recommendations ADD COLUMN suppressed_until DATETIME"))
            if "suppression_notes" not in ocols:
                conn.execute(text("ALTER TABLE operational_recommendations ADD COLUMN suppression_notes TEXT"))

        if not insp.has_table("recommendation_suppressions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE recommendation_suppressions (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        recommendation_key VARCHAR(255),
                        category VARCHAR(64),
                        contract_id VARCHAR(36),
                        site_id VARCHAR(36),
                        suppressed_until DATETIME NOT NULL,
                        notes TEXT,
                        created_by_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )

        if not insp.has_table("recommendation_occurrence_events"):
            conn.execute(
                text(
                    """
                    CREATE TABLE recommendation_occurrence_events (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        recommendation_key VARCHAR(255) NOT NULL,
                        recorded_at DATETIME NOT NULL
                    )
                    """
                )
            )

        if not insp.has_table("contract_performance_snapshots"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_performance_snapshots (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        period_window VARCHAR(32) NOT NULL,
                        snapshot_at DATETIME NOT NULL,
                        currency VARCHAR(3) NOT NULL DEFAULT 'GBP',
                        contract_value_at_snapshot FLOAT,
                        revenue_invoiced FLOAT NOT NULL DEFAULT 0,
                        revenue_paid FLOAT NOT NULL DEFAULT 0,
                        revenue_unpaid FLOAT NOT NULL DEFAULT 0,
                        revenue_overdue FLOAT NOT NULL DEFAULT 0,
                        material_cost FLOAT NOT NULL DEFAULT 0,
                        labour_cost FLOAT NOT NULL DEFAULT 0,
                        total_cost FLOAT NOT NULL DEFAULT 0,
                        gross_margin_amount FLOAT NOT NULL DEFAULT 0,
                        gross_margin_percent FLOAT,
                        planned_job_count INTEGER NOT NULL DEFAULT 0,
                        reactive_job_count INTEGER NOT NULL DEFAULT 0,
                        completed_job_count INTEGER NOT NULL DEFAULT 0,
                        overdue_ppm_count INTEGER NOT NULL DEFAULT 0,
                        sla_breach_count INTEGER NOT NULL DEFAULT 0,
                        open_recommendation_count INTEGER NOT NULL DEFAULT 0,
                        jobs_without_costing_snapshot INTEGER NOT NULL DEFAULT 0,
                        completed_jobs_missing_snapshot INTEGER NOT NULL DEFAULT 0,
                        health_score INTEGER NOT NULL DEFAULT 0,
                        health_status VARCHAR(24) NOT NULL DEFAULT 'unknown',
                        renewal_status VARCHAR(24) NOT NULL DEFAULT 'unknown',
                        renewal_risk_level VARCHAR(16) NOT NULL DEFAULT 'unknown',
                        renewal_opportunity_level VARCHAR(16) NOT NULL DEFAULT 'unknown',
                        renewal_review_due INTEGER NOT NULL DEFAULT 0,
                        avg_response_minutes FLOAT,
                        avg_attendance_minutes FLOAT,
                        avg_resolution_minutes FLOAT,
                        warnings_json TEXT NOT NULL DEFAULT '[]',
                        calculation_basis_json TEXT NOT NULL DEFAULT '{}',
                        renewal_reasons_json TEXT NOT NULL DEFAULT '[]',
                        health_components_json TEXT NOT NULL DEFAULT '{}',
                        site_burden_json TEXT NOT NULL DEFAULT '[]',
                        asset_burden_json TEXT NOT NULL DEFAULT '[]',
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )

        if not insp.has_table("labour_rate_profiles"):
            conn.execute(
                text(
                    """
                    CREATE TABLE labour_rate_profiles (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        name VARCHAR(128) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        base_hourly_rate FLOAT NOT NULL,
                        overtime_hourly_rate FLOAT,
                        doubletime_hourly_rate FLOAT,
                        travel_hourly_rate FLOAT,
                        out_of_hours_hourly_rate FLOAT,
                        minimum_billable_minutes INTEGER,
                        default_profile INTEGER NOT NULL DEFAULT 0,
                        applies_to_role_name VARCHAR(64),
                        applies_to_engineer_id VARCHAR(36),
                        applies_to_contract_id VARCHAR(36),
                        notes TEXT,
                        work_window_start_minutes_utc INTEGER,
                        work_window_end_minutes_utc INTEGER,
                        overtime_threshold_minutes_per_day INTEGER,
                        doubletime_threshold_minutes_per_day INTEGER,
                        weekend_uses_doubletime_rate INTEGER NOT NULL DEFAULT 0,
                        travel_costing_enabled INTEGER NOT NULL DEFAULT 1,
                        holiday_placeholder_json TEXT NOT NULL DEFAULT '[]',
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )

        if insp.has_table("job_cost_snapshots"):
            jcols = {c["name"] for c in insp.get_columns("job_cost_snapshots")}
            for col, ddl in (
                ("regular_labour_minutes", "INTEGER NOT NULL DEFAULT 0"),
                ("overtime_labour_minutes", "INTEGER NOT NULL DEFAULT 0"),
                ("doubletime_labour_minutes", "INTEGER NOT NULL DEFAULT 0"),
                ("travel_labour_minutes", "INTEGER NOT NULL DEFAULT 0"),
                ("out_of_hours_labour_minutes", "INTEGER NOT NULL DEFAULT 0"),
                ("break_minutes_excluded", "INTEGER NOT NULL DEFAULT 0"),
                ("regular_labour_cost", "FLOAT NOT NULL DEFAULT 0"),
                ("doubletime_labour_cost", "FLOAT NOT NULL DEFAULT 0"),
                ("out_of_hours_labour_cost", "FLOAT NOT NULL DEFAULT 0"),
                ("labour_rate_profile_id", "VARCHAR(36)"),
                ("labour_cost_warnings_json", "TEXT NOT NULL DEFAULT '[]'"),
                ("labour_cost_completeness", "VARCHAR(16) NOT NULL DEFAULT 'unavailable'"),
                ("labour_rule_set_id", "VARCHAR(36)"),
                ("holiday_calendar_id", "VARCHAR(36)"),
                ("labour_local_timezone_name", "VARCHAR(64)"),
                ("labour_rules_completeness_status", "VARCHAR(32)"),
                ("labour_rules_attribution_json", "TEXT NOT NULL DEFAULT '{}'"),
            ):
                if col not in jcols:
                    conn.execute(text(f"ALTER TABLE job_cost_snapshots ADD COLUMN {col} {ddl}"))

        if not insp.has_table("stored_documents"):
            conn.execute(
                text(
                    """
                    CREATE TABLE stored_documents (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        document_type VARCHAR(64) NOT NULL,
                        filename VARCHAR(255) NOT NULL,
                        content_type VARCHAR(128) NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        storage_key VARCHAR(512) NOT NULL UNIQUE,
                        storage_provider VARCHAR(32) NOT NULL,
                        checksum_sha256 VARCHAR(64),
                        related_job_id VARCHAR(36),
                        related_site_id VARCHAR(36),
                        related_asset_id VARCHAR(36),
                        related_contract_id VARCHAR(36),
                        related_invoice_id VARCHAR(36),
                        related_certificate_id VARCHAR(36),
                        uploaded_by_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL,
                        source_type VARCHAR(24) NOT NULL,
                        visibility_scope VARCHAR(32) NOT NULL,
                        status VARCHAR(24) NOT NULL,
                        metadata_json TEXT,
                        FOREIGN KEY(related_job_id) REFERENCES jobs (id),
                        FOREIGN KEY(related_site_id) REFERENCES sites (id),
                        FOREIGN KEY(related_asset_id) REFERENCES assets (id),
                        FOREIGN KEY(related_contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(related_invoice_id) REFERENCES invoices (id),
                        FOREIGN KEY(related_certificate_id) REFERENCES certificates (id),
                        FOREIGN KEY(uploaded_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_stored_documents_document_type ON stored_documents (document_type)"))
            conn.execute(text("CREATE INDEX ix_stored_documents_storage_key ON stored_documents (storage_key)"))
            conn.execute(text("CREATE INDEX ix_stored_documents_related_job_id ON stored_documents (related_job_id)"))

        if not insp.has_table("document_access_logs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE document_access_logs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        document_id VARCHAR(36),
                        user_id VARCHAR(36),
                        customer_id VARCHAR(36),
                        access_type VARCHAR(32) NOT NULL,
                        source_context VARCHAR(16) NOT NULL,
                        created_at DATETIME NOT NULL,
                        remote_ip VARCHAR(64),
                        user_agent VARCHAR(512),
                        status VARCHAR(16) NOT NULL,
                        reason VARCHAR(255),
                        FOREIGN KEY(user_id) REFERENCES users (id),
                        FOREIGN KEY(customer_id) REFERENCES customers (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_document_access_logs_document_id ON document_access_logs (document_id)"))

        if not insp.has_table("field_equipment"):
            conn.execute(
                text(
                    """
                    CREATE TABLE field_equipment (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        equipment_code VARCHAR(64) NOT NULL UNIQUE,
                        name VARCHAR(255) NOT NULL,
                        equipment_type VARCHAR(128) NOT NULL,
                        category VARCHAR(128) NOT NULL DEFAULT 'general',
                        manufacturer VARCHAR(255),
                        model VARCHAR(255),
                        serial_number VARCHAR(128),
                        status VARCHAR(32) NOT NULL DEFAULT 'available',
                        ownership_type VARCHAR(32) NOT NULL DEFAULT 'owned',
                        current_location_type VARCHAR(32) NOT NULL DEFAULT 'warehouse',
                        current_location_id VARCHAR(64),
                        assigned_engineer_id VARCHAR(36),
                        assigned_vehicle_id VARCHAR(64),
                        assigned_site_id VARCHAR(36),
                        purchase_date DATETIME,
                        warranty_expiry DATETIME,
                        service_due_date DATETIME,
                        inspection_due_date DATETIME,
                        calibration_required INTEGER NOT NULL DEFAULT 0,
                        calibration_due_date DATETIME,
                        calibration_status VARCHAR(24) NOT NULL DEFAULT 'not_required',
                        notes TEXT,
                        metadata_json TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(assigned_engineer_id) REFERENCES users (id),
                        FOREIGN KEY(assigned_site_id) REFERENCES sites (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_field_equipment_equipment_type ON field_equipment (equipment_type)"))
            conn.execute(text("CREATE INDEX ix_field_equipment_status ON field_equipment (status)"))

        if not insp.has_table("equipment_movements"):
            conn.execute(
                text(
                    """
                    CREATE TABLE equipment_movements (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        equipment_id VARCHAR(36) NOT NULL,
                        movement_type VARCHAR(64) NOT NULL,
                        prev_location_type VARCHAR(32),
                        prev_location_id VARCHAR(64),
                        new_location_type VARCHAR(32),
                        new_location_id VARCHAR(64),
                        prev_status VARCHAR(32),
                        new_status VARCHAR(32),
                        assigned_engineer_id_after VARCHAR(36),
                        assigned_vehicle_id_after VARCHAR(64),
                        assigned_site_id_after VARCHAR(36),
                        notes TEXT,
                        performed_by_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(equipment_id) REFERENCES field_equipment (id),
                        FOREIGN KEY(performed_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )

        if not insp.has_table("job_equipment_requirements"):
            conn.execute(
                text(
                    """
                    CREATE TABLE job_equipment_requirements (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        job_id VARCHAR(36) NOT NULL,
                        equipment_type VARCHAR(128) NOT NULL,
                        category VARCHAR(128) NOT NULL DEFAULT 'general',
                        specific_equipment_id VARCHAR(36),
                        calibration_required INTEGER NOT NULL DEFAULT 0,
                        mandatory INTEGER NOT NULL DEFAULT 1,
                        quantity INTEGER NOT NULL DEFAULT 1,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(job_id) REFERENCES jobs (id),
                        FOREIGN KEY(specific_equipment_id) REFERENCES field_equipment (id)
                    )
                    """
                )
            )

        if not insp.has_table("equipment_calibration_records"):
            conn.execute(
                text(
                    """
                    CREATE TABLE equipment_calibration_records (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        equipment_id VARCHAR(36) NOT NULL,
                        performed_at DATETIME NOT NULL,
                        next_due_date DATETIME,
                        certificate_document_id VARCHAR(36),
                        notes TEXT,
                        performed_by_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(equipment_id) REFERENCES field_equipment (id),
                        FOREIGN KEY(certificate_document_id) REFERENCES stored_documents (id),
                        FOREIGN KEY(performed_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )

        if not insp.has_table("equipment_inspection_records"):
            conn.execute(
                text(
                    """
                    CREATE TABLE equipment_inspection_records (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        equipment_id VARCHAR(36) NOT NULL,
                        performed_at DATETIME NOT NULL,
                        next_inspection_due_date DATETIME,
                        next_service_due_date DATETIME,
                        certificate_document_id VARCHAR(36),
                        notes TEXT,
                        performed_by_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(equipment_id) REFERENCES field_equipment (id),
                        FOREIGN KEY(certificate_document_id) REFERENCES stored_documents (id),
                        FOREIGN KEY(performed_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )

        if not insp.has_table("vehicle_inspections"):
            conn.execute(
                text(
                    """
                    CREATE TABLE vehicle_inspections (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        vehicle_id VARCHAR(64) NOT NULL,
                        engineer_id VARCHAR(36) NOT NULL,
                        inspection_date DATE NOT NULL,
                        performed_at DATETIME NOT NULL,
                        odometer FLOAT,
                        latitude FLOAT,
                        longitude FLOAT,
                        overall_status VARCHAR(24) NOT NULL,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(engineer_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_vehicle_inspections_vehicle_id ON vehicle_inspections (vehicle_id)"))
            conn.execute(text("CREATE INDEX ix_vehicle_inspections_inspection_date ON vehicle_inspections (inspection_date)"))

        if not insp.has_table("vehicle_inspection_items"):
            conn.execute(
                text(
                    """
                    CREATE TABLE vehicle_inspection_items (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        inspection_id VARCHAR(36) NOT NULL,
                        item_code VARCHAR(64) NOT NULL,
                        item_label VARCHAR(255) NOT NULL,
                        result VARCHAR(16) NOT NULL,
                        notes TEXT,
                        photo_document_id VARCHAR(36),
                        fail_criticality VARCHAR(16) NOT NULL DEFAULT 'minor',
                        FOREIGN KEY(inspection_id) REFERENCES vehicle_inspections (id),
                        FOREIGN KEY(photo_document_id) REFERENCES stored_documents (id)
                    )
                    """
                )
            )

        if not insp.has_table("vehicle_defects"):
            conn.execute(
                text(
                    """
                    CREATE TABLE vehicle_defects (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        vehicle_id VARCHAR(64) NOT NULL,
                        inspection_id VARCHAR(36),
                        defect_type VARCHAR(64) NOT NULL,
                        severity VARCHAR(16) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        status VARCHAR(16) NOT NULL DEFAULT 'open',
                        reported_at DATETIME NOT NULL,
                        reported_by_user_id VARCHAR(36),
                        resolved_at DATETIME,
                        resolved_by_user_id VARCHAR(36),
                        resolution_notes TEXT,
                        FOREIGN KEY(inspection_id) REFERENCES vehicle_inspections (id),
                        FOREIGN KEY(reported_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(resolved_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_vehicle_defects_vehicle_id ON vehicle_defects (vehicle_id)"))
            conn.execute(text("CREATE INDEX ix_vehicle_defects_status ON vehicle_defects (status)"))

        if not insp.has_table("recommendation_action_suggestions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE recommendation_action_suggestions (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        recommendation_id VARCHAR(36) NOT NULL,
                        action_type VARCHAR(64) NOT NULL,
                        action_label VARCHAR(255) NOT NULL,
                        action_description TEXT NOT NULL,
                        action_status VARCHAR(24) NOT NULL DEFAULT 'available',
                        preview_json TEXT,
                        input_schema_json TEXT,
                        requires_confirmation INTEGER NOT NULL DEFAULT 1,
                        requires_override_reason INTEGER NOT NULL DEFAULT 0,
                        risk_level VARCHAR(16) NOT NULL DEFAULT 'medium',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(recommendation_id) REFERENCES operational_recommendations (id),
                        CONSTRAINT uq_rec_action_suggestion_type UNIQUE (recommendation_id, action_type)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_rec_action_suggestions_rec_id ON recommendation_action_suggestions (recommendation_id)")
            )
            conn.execute(
                text("CREATE INDEX ix_rec_action_suggestions_action_type ON recommendation_action_suggestions (action_type)")
            )

        if not insp.has_table("recommendation_action_decisions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE recommendation_action_decisions (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        recommendation_id VARCHAR(36) NOT NULL,
                        action_suggestion_id VARCHAR(36),
                        decision_type VARCHAR(24) NOT NULL,
                        decided_by_user_id VARCHAR(36) NOT NULL,
                        decided_at DATETIME NOT NULL,
                        decision_notes TEXT,
                        override_reason TEXT,
                        preview_snapshot_json TEXT,
                        execution_result_json TEXT,
                        execution_status VARCHAR(24),
                        FOREIGN KEY(recommendation_id) REFERENCES operational_recommendations (id),
                        FOREIGN KEY(action_suggestion_id) REFERENCES recommendation_action_suggestions (id),
                        FOREIGN KEY(decided_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_rec_action_decisions_rec_id ON recommendation_action_decisions (recommendation_id)")
            )
            conn.execute(
                text(
                    "CREATE INDEX ix_rec_action_decisions_suggestion_id ON recommendation_action_decisions (action_suggestion_id)"
                )
            )

        if insp.has_table("contracts"):
            cols = {c["name"] for c in insp.get_columns("contracts")}
            for col, ddl in (
                ("renewal_status", "VARCHAR(32) NOT NULL DEFAULT 'not_due'"),
                ("renewal_review_due_at", "DATETIME"),
                ("renewal_review_last_opened_at", "DATETIME"),
                ("renewal_decision", "VARCHAR(32)"),
                ("repricing_required", "INTEGER NOT NULL DEFAULT 0"),
                ("account_attention_level", "VARCHAR(16) NOT NULL DEFAULT 'normal'"),
                ("churn_risk_level", "VARCHAR(16)"),
                ("communication_locale", "VARCHAR(16)"),
            ):
                if col not in cols:
                    conn.execute(text(f"ALTER TABLE contracts ADD COLUMN {col} {ddl}"))

        if not insp.has_table("contract_reviews"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_reviews (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        review_type VARCHAR(32) NOT NULL,
                        status VARCHAR(32) NOT NULL DEFAULT 'open',
                        triggered_by VARCHAR(32) NOT NULL DEFAULT 'manual',
                        triggered_reason TEXT NOT NULL,
                        opened_at DATETIME NOT NULL,
                        due_at DATETIME,
                        assigned_to_user_id VARCHAR(36),
                        priority VARCHAR(16) NOT NULL DEFAULT 'normal',
                        summary TEXT NOT NULL,
                        notes TEXT,
                        decision VARCHAR(32),
                        decided_at DATETIME,
                        decided_by_user_id VARCHAR(36),
                        metadata_json TEXT,
                        source_recommendation_id VARCHAR(36),
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(assigned_to_user_id) REFERENCES users (id),
                        FOREIGN KEY(decided_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(source_recommendation_id) REFERENCES operational_recommendations (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_contract_reviews_contract_id ON contract_reviews (contract_id)"))
            conn.execute(text("CREATE INDEX ix_contract_reviews_review_type ON contract_reviews (review_type)"))
            conn.execute(text("CREATE INDEX ix_contract_reviews_status ON contract_reviews (status)"))

        if not insp.has_table("contract_repricing_reviews"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_repricing_reviews (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        review_id VARCHAR(36) NOT NULL,
                        current_contract_value FLOAT,
                        proposed_contract_value FLOAT,
                        repricing_reason_codes_json TEXT NOT NULL DEFAULT '[]',
                        margin_summary_json TEXT,
                        burden_summary_json TEXT,
                        recommendation_basis_json TEXT,
                        customer_risk_level VARCHAR(16) NOT NULL DEFAULT 'medium',
                        approved INTEGER,
                        approved_at DATETIME,
                        approved_by_user_id VARCHAR(36),
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(review_id) REFERENCES contract_reviews (id),
                        FOREIGN KEY(approved_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_repricing_contract ON contract_repricing_reviews (contract_id)"))
            conn.execute(text("CREATE INDEX ix_repricing_review ON contract_repricing_reviews (review_id)"))

        if not insp.has_table("contract_commercial_action_logs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_commercial_action_logs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        review_id VARCHAR(36),
                        action_type VARCHAR(64) NOT NULL,
                        action_summary TEXT NOT NULL,
                        performed_by_user_id VARCHAR(36) NOT NULL,
                        performed_at DATETIME NOT NULL,
                        notes TEXT,
                        payload_json TEXT,
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(review_id) REFERENCES contract_reviews (id),
                        FOREIGN KEY(performed_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_cc_action_contract ON contract_commercial_action_logs (contract_id)"))
            conn.execute(text("CREATE INDEX ix_cc_action_review ON contract_commercial_action_logs (review_id)"))

        if not insp.has_table("approval_requests"):
            conn.execute(
                text(
                    """
                    CREATE TABLE approval_requests (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        approval_type VARCHAR(64) NOT NULL,
                        target_entity_type VARCHAR(64) NOT NULL,
                        target_entity_id VARCHAR(64) NOT NULL,
                        requested_by_user_id VARCHAR(36) NOT NULL,
                        assigned_to_user_id VARCHAR(36),
                        status VARCHAR(24) NOT NULL DEFAULT 'pending',
                        reason TEXT NOT NULL,
                        payload_json TEXT,
                        created_at DATETIME NOT NULL,
                        decided_at DATETIME,
                        decided_by_user_id VARCHAR(36),
                        decision_notes TEXT,
                        execution_result_json TEXT,
                        FOREIGN KEY(requested_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(assigned_to_user_id) REFERENCES users (id),
                        FOREIGN KEY(decided_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_approval_req_status ON approval_requests (status)"))
            conn.execute(text("CREATE INDEX ix_approval_req_type ON approval_requests (approval_type)"))
            conn.execute(text("CREATE INDEX ix_approval_req_target ON approval_requests (target_entity_type, target_entity_id)"))
            conn.execute(text("CREATE INDEX ix_approval_req_requester ON approval_requests (requested_by_user_id)"))

        if not insp.has_table("approval_audit_logs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE approval_audit_logs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        approval_request_id VARCHAR(36) NOT NULL,
                        event_type VARCHAR(32) NOT NULL,
                        actor_user_id VARCHAR(36),
                        notes TEXT,
                        detail_json TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(approval_request_id) REFERENCES approval_requests (id),
                        FOREIGN KEY(actor_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_approval_audit_req ON approval_audit_logs (approval_request_id)"))

        if not insp.has_table("contract_repricing_proposals"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_repricing_proposals (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        repricing_review_id VARCHAR(36) NOT NULL,
                        review_id VARCHAR(36),
                        proposal_status VARCHAR(32) NOT NULL DEFAULT 'generated',
                        proposal_reference VARCHAR(64) NOT NULL UNIQUE,
                        currency VARCHAR(3) NOT NULL DEFAULT 'GBP',
                        current_contract_value FLOAT,
                        proposed_contract_value FLOAT,
                        effective_date DATETIME,
                        validity_end_date DATETIME,
                        generated_at DATETIME NOT NULL,
                        generated_by_user_id VARCHAR(36),
                        approved_at DATETIME,
                        approved_by_user_id VARCHAR(36),
                        ready_for_customer_at DATETIME,
                        superseded_by_proposal_id VARCHAR(36),
                        notes TEXT,
                        pricing_basis_json TEXT NOT NULL DEFAULT '{}',
                        change_summary_json TEXT NOT NULL DEFAULT '{}',
                        metadata_json TEXT,
                        stored_document_id VARCHAR(36),
                        customer_release_status VARCHAR(32) NOT NULL DEFAULT 'not_released',
                        released_to_customer_at DATETIME,
                        released_by_user_id VARCHAR(36),
                        customer_viewed_at DATETIME,
                        customer_responded_at DATETIME,
                        customer_response_status VARCHAR(32),
                        customer_response_notes TEXT,
                        customer_response_by_contact VARCHAR(255),
                        customer_expiry_at DATETIME,
                        portal_visibility_scope VARCHAR(32),
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(repricing_review_id) REFERENCES contract_repricing_reviews (id),
                        FOREIGN KEY(review_id) REFERENCES contract_reviews (id),
                        FOREIGN KEY(generated_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(approved_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(superseded_by_proposal_id) REFERENCES contract_repricing_proposals (id),
                        FOREIGN KEY(stored_document_id) REFERENCES stored_documents (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_repricing_prop_contract ON contract_repricing_proposals (contract_id)"))
            conn.execute(text("CREATE INDEX ix_repricing_prop_status ON contract_repricing_proposals (proposal_status)"))
            conn.execute(text("CREATE INDEX ix_repricing_prop_review_row ON contract_repricing_proposals (repricing_review_id)"))

        if not insp.has_table("contract_repricing_proposal_lines"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_repricing_proposal_lines (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        proposal_id VARCHAR(36) NOT NULL,
                        line_type VARCHAR(64) NOT NULL,
                        code VARCHAR(64),
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        quantity FLOAT NOT NULL DEFAULT 1.0,
                        unit VARCHAR(32) NOT NULL DEFAULT 'ea',
                        current_unit_price FLOAT,
                        proposed_unit_price FLOAT,
                        current_line_total FLOAT,
                        proposed_line_total FLOAT NOT NULL,
                        variance_amount FLOAT,
                        variance_percent FLOAT,
                        justification_json TEXT,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(proposal_id) REFERENCES contract_repricing_proposals (id) ON DELETE CASCADE
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_repricing_prop_line_proposal ON contract_repricing_proposal_lines (proposal_id)"))

        if insp.has_table("contract_repricing_proposals"):
            cols = {c["name"] for c in insp.get_columns("contract_repricing_proposals")}
            _add = [
                ("customer_release_status", "VARCHAR(32) NOT NULL DEFAULT 'not_released'"),
                ("released_to_customer_at", "DATETIME"),
                ("released_by_user_id", "VARCHAR(36)"),
                ("customer_viewed_at", "DATETIME"),
                ("customer_responded_at", "DATETIME"),
                ("customer_response_status", "VARCHAR(32)"),
                ("customer_response_notes", "TEXT"),
                ("customer_response_by_contact", "VARCHAR(255)"),
                ("customer_expiry_at", "DATETIME"),
                ("portal_visibility_scope", "VARCHAR(32)"),
            ]
            for name, ddl in _add:
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE contract_repricing_proposals ADD COLUMN {name} {ddl}"))

        if not insp.has_table("proposal_customer_responses"):
            conn.execute(
                text(
                    """
                    CREATE TABLE proposal_customer_responses (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        proposal_id VARCHAR(36) NOT NULL,
                        response_type VARCHAR(32) NOT NULL,
                        responded_at DATETIME NOT NULL,
                        responded_by_customer_id VARCHAR(36) NOT NULL,
                        notes TEXT,
                        contact_reference VARCHAR(255),
                        metadata_json TEXT,
                        FOREIGN KEY(proposal_id) REFERENCES contract_repricing_proposals (id) ON DELETE CASCADE,
                        FOREIGN KEY(responded_by_customer_id) REFERENCES customers (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_prop_cust_resp_proposal ON proposal_customer_responses (proposal_id)"))
            conn.execute(
                text("CREATE INDEX ix_prop_cust_resp_customer ON proposal_customer_responses (responded_by_customer_id)")
            )

        if not insp.has_table("automation_runs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE automation_runs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        automation_type VARCHAR(64) NOT NULL,
                        trigger_type VARCHAR(32) NOT NULL,
                        trigger_entity_type VARCHAR(64) NOT NULL,
                        trigger_entity_id VARCHAR(64) NOT NULL,
                        source_recommendation_id VARCHAR(36),
                        source_event_type VARCHAR(64),
                        status VARCHAR(24) NOT NULL DEFAULT 'created',
                        created_at DATETIME NOT NULL,
                        completed_at DATETIME,
                        created_by_system INTEGER NOT NULL DEFAULT 1,
                        result_summary TEXT NOT NULL DEFAULT '',
                        payload_json TEXT NOT NULL DEFAULT '{}',
                        warnings_json TEXT,
                        draft_entity_type VARCHAR(64),
                        draft_entity_id VARCHAR(64),
                        performed_by_user_id VARCHAR(36),
                        FOREIGN KEY(source_recommendation_id) REFERENCES operational_recommendations (id),
                        FOREIGN KEY(performed_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_automation_runs_type ON automation_runs (automation_type)"))
            conn.execute(text("CREATE INDEX ix_automation_runs_status ON automation_runs (status)"))
            conn.execute(text("CREATE INDEX ix_automation_runs_trigger ON automation_runs (trigger_entity_type, trigger_entity_id)"))
            conn.execute(text("CREATE INDEX ix_automation_runs_rec ON automation_runs (source_recommendation_id)"))

        if not insp.has_table("internal_follow_up_tasks"):
            conn.execute(
                text(
                    """
                    CREATE TABLE internal_follow_up_tasks (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        task_type VARCHAR(64) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        summary TEXT NOT NULL,
                        status VARCHAR(24) NOT NULL DEFAULT 'open',
                        priority VARCHAR(16) NOT NULL DEFAULT 'normal',
                        related_entity_type VARCHAR(64) NOT NULL,
                        related_entity_id VARCHAR(64) NOT NULL,
                        source_recommendation_id VARCHAR(36),
                        source_automation_run_id VARCHAR(36),
                        assigned_to_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL,
                        due_at DATETIME,
                        completed_at DATETIME,
                        notes TEXT,
                        payload_json TEXT,
                        FOREIGN KEY(source_recommendation_id) REFERENCES operational_recommendations (id),
                        FOREIGN KEY(source_automation_run_id) REFERENCES automation_runs (id),
                        FOREIGN KEY(assigned_to_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_follow_up_tasks_type ON internal_follow_up_tasks (task_type)"))
            conn.execute(text("CREATE INDEX ix_follow_up_tasks_status ON internal_follow_up_tasks (status)"))
            conn.execute(text("CREATE INDEX ix_follow_up_tasks_related ON internal_follow_up_tasks (related_entity_type, related_entity_id)"))

        if not insp.has_table("user_permission_grants"):
            conn.execute(
                text(
                    """
                    CREATE TABLE user_permission_grants (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL,
                        permission_key VARCHAR(64) NOT NULL,
                        effect VARCHAR(16) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        expires_at DATETIME,
                        FOREIGN KEY(user_id) REFERENCES users (id),
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id),
                        UNIQUE (user_id, permission_key)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_user_perm_grant_user ON user_permission_grants (user_id)"))
            conn.execute(text("CREATE INDEX ix_user_perm_grant_key ON user_permission_grants (permission_key)"))

        if not insp.has_table("permission_grant_audit_logs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE permission_grant_audit_logs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        grant_id VARCHAR(36),
                        actor_user_id VARCHAR(36),
                        target_user_id VARCHAR(36) NOT NULL,
                        permission_key VARCHAR(64) NOT NULL,
                        action VARCHAR(24) NOT NULL,
                        old_effect VARCHAR(16),
                        new_effect VARCHAR(16),
                        old_active INTEGER,
                        new_active INTEGER,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(grant_id) REFERENCES user_permission_grants (id),
                        FOREIGN KEY(actor_user_id) REFERENCES users (id),
                        FOREIGN KEY(target_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_perm_grant_audit_target ON permission_grant_audit_logs (target_user_id)"))

        if not insp.has_table("contract_amendments"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_amendments (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        source_proposal_id VARCHAR(36),
                        source_review_id VARCHAR(36),
                        amendment_type VARCHAR(32) NOT NULL,
                        status VARCHAR(32) NOT NULL DEFAULT 'draft',
                        amendment_reference VARCHAR(64) NOT NULL UNIQUE,
                        current_contract_value FLOAT,
                        proposed_contract_value FLOAT,
                        effective_date DATETIME NOT NULL,
                        activated_at DATETIME,
                        activated_by_user_id VARCHAR(36),
                        approved_at DATETIME,
                        approved_by_user_id VARCHAR(36),
                        approval_required INTEGER NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        notes TEXT,
                        pricing_basis_json TEXT,
                        change_summary_json TEXT,
                        prior_contract_snapshot_json TEXT NOT NULL,
                        resulting_contract_snapshot_json TEXT,
                        metadata_json TEXT,
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(source_proposal_id) REFERENCES contract_repricing_proposals (id),
                        FOREIGN KEY(source_review_id) REFERENCES contract_reviews (id),
                        FOREIGN KEY(activated_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(approved_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_contract_amendment_contract ON contract_amendments (contract_id)"))
            conn.execute(text("CREATE INDEX ix_contract_amendment_status ON contract_amendments (status)"))
            conn.execute(text("CREATE INDEX ix_contract_amendment_proposal ON contract_amendments (source_proposal_id)"))
            conn.execute(text("CREATE INDEX ix_contract_amendment_effective ON contract_amendments (effective_date)"))

        if insp.has_table("contract_amendments"):
            cols_am = {c["name"] for c in insp.get_columns("contract_amendments")}
            if "resulting_contract_version_id" not in cols_am:
                conn.execute(
                    text("ALTER TABLE contract_amendments ADD COLUMN resulting_contract_version_id VARCHAR(36)")
                )

        if not insp.has_table("contract_versions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_versions (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        version_number INTEGER NOT NULL,
                        source_amendment_id VARCHAR(36),
                        version_type VARCHAR(32) NOT NULL,
                        effective_from DATETIME NOT NULL,
                        effective_to DATETIME,
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        contract_value FLOAT,
                        renewal_status VARCHAR(32),
                        renewal_decision VARCHAR(32),
                        repricing_required INTEGER,
                        account_attention_level VARCHAR(16),
                        churn_risk_level VARCHAR(16),
                        snapshot_json TEXT NOT NULL,
                        change_summary_json TEXT,
                        notes TEXT,
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(source_amendment_id) REFERENCES contract_amendments (id),
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id),
                        UNIQUE (contract_id, version_number)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_contract_versions_contract ON contract_versions (contract_id)"))
            conn.execute(text("CREATE INDEX ix_contract_versions_amendment ON contract_versions (source_amendment_id)"))
            conn.execute(text("CREATE INDEX ix_contract_versions_effective_from ON contract_versions (effective_from)"))

        if not insp.has_table("contract_activation_runs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_activation_runs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        amendment_id VARCHAR(36) NOT NULL,
                        contract_id VARCHAR(36) NOT NULL,
                        run_type VARCHAR(24) NOT NULL,
                        status VARCHAR(24) NOT NULL,
                        started_at DATETIME NOT NULL,
                        completed_at DATETIME,
                        triggered_by_user_id VARCHAR(36),
                        attempt_number INTEGER NOT NULL DEFAULT 1,
                        result_summary TEXT,
                        error_json TEXT,
                        idempotency_key VARCHAR(128),
                        notes TEXT,
                        FOREIGN KEY(amendment_id) REFERENCES contract_amendments (id),
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(triggered_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_contract_act_run_amendment ON contract_activation_runs (amendment_id)"))
            conn.execute(text("CREATE INDEX ix_contract_act_run_contract ON contract_activation_runs (contract_id)"))
            conn.execute(text("CREATE INDEX ix_contract_act_run_status ON contract_activation_runs (status)"))
            conn.execute(text("CREATE INDEX ix_contract_act_run_idem ON contract_activation_runs (idempotency_key)"))

        if not insp.has_table("contract_activation_confirmations"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_activation_confirmations (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        amendment_id VARCHAR(36) NOT NULL,
                        contract_version_id VARCHAR(36),
                        source_proposal_id VARCHAR(36),
                        status VARCHAR(32) NOT NULL,
                        confirmation_reference VARCHAR(96) NOT NULL,
                        effective_date DATETIME NOT NULL,
                        activated_at DATETIME NOT NULL,
                        confirmation_generated_at DATETIME,
                        released_to_customer_at DATETIME,
                        released_by_user_id VARCHAR(36),
                        customer_viewed_at DATETIME,
                        customer_acknowledged_at DATETIME,
                        customer_acknowledged_by_contact VARCHAR(255),
                        customer_acknowledgement_notes TEXT,
                        portal_visibility_scope VARCHAR(64),
                        stored_document_id VARCHAR(36),
                        summary_json TEXT,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(amendment_id) REFERENCES contract_amendments (id),
                        FOREIGN KEY(contract_version_id) REFERENCES contract_versions (id),
                        FOREIGN KEY(source_proposal_id) REFERENCES contract_repricing_proposals (id),
                        FOREIGN KEY(released_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(stored_document_id) REFERENCES stored_documents (id),
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id),
                        UNIQUE (confirmation_reference)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_activation_conf_contract ON contract_activation_confirmations (contract_id)")
            )
            conn.execute(
                text("CREATE INDEX ix_activation_conf_amendment ON contract_activation_confirmations (amendment_id)")
            )
            conn.execute(text("CREATE INDEX ix_activation_conf_status ON contract_activation_confirmations (status)"))

        if not insp.has_table("contract_customer_communications"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_customer_communications (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        contract_id VARCHAR(36) NOT NULL,
                        source_entity_type VARCHAR(64) NOT NULL,
                        source_entity_id VARCHAR(36) NOT NULL,
                        communication_type VARCHAR(64) NOT NULL,
                        status VARCHAR(24) NOT NULL,
                        channel VARCHAR(24) NOT NULL,
                        subject VARCHAR(512),
                        body_text TEXT,
                        body_html TEXT,
                        template_key VARCHAR(96),
                        recipient_customer_id VARCHAR(36),
                        recipient_contact_reference VARCHAR(255),
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        ready_at DATETIME,
                        sent_at DATETIME,
                        failed_at DATETIME,
                        cancelled_at DATETIME,
                        approved_at DATETIME,
                        approved_by_user_id VARCHAR(36),
                        requires_approval INTEGER NOT NULL DEFAULT 0,
                        error_json TEXT,
                        metadata_json TEXT,
                        stored_document_id VARCHAR(36),
                        source_proposal_id VARCHAR(36),
                        source_amendment_id VARCHAR(36),
                        source_activation_confirmation_id VARCHAR(36),
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(recipient_customer_id) REFERENCES customers (id),
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(approved_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(stored_document_id) REFERENCES stored_documents (id),
                        FOREIGN KEY(source_proposal_id) REFERENCES contract_repricing_proposals (id),
                        FOREIGN KEY(source_amendment_id) REFERENCES contract_amendments (id),
                        FOREIGN KEY(source_activation_confirmation_id) REFERENCES contract_activation_confirmations (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_ccc_contract ON contract_customer_communications (contract_id)"))
            conn.execute(text("CREATE INDEX ix_ccc_status ON contract_customer_communications (status)"))
            conn.execute(text("CREATE INDEX ix_ccc_type ON contract_customer_communications (communication_type)"))
            conn.execute(text("CREATE INDEX ix_ccc_source ON contract_customer_communications (source_entity_type, source_entity_id)"))

        if not insp.has_table("contract_customer_communication_deliveries"):
            conn.execute(
                text(
                    """
                    CREATE TABLE contract_customer_communication_deliveries (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        communication_id VARCHAR(36) NOT NULL,
                        channel VARCHAR(24) NOT NULL,
                        provider_name VARCHAR(64) NOT NULL,
                        provider_message_id VARCHAR(255),
                        attempt_number INTEGER NOT NULL,
                        started_at DATETIME NOT NULL,
                        completed_at DATETIME,
                        status VARCHAR(24) NOT NULL,
                        recipient_address VARCHAR(512),
                        error_code VARCHAR(64),
                        error_message TEXT,
                        response_payload_json TEXT,
                        FOREIGN KEY(communication_id) REFERENCES contract_customer_communications (id)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_ccd_comm ON contract_customer_communication_deliveries (communication_id)")
            )
            conn.execute(text("CREATE INDEX ix_ccd_status ON contract_customer_communication_deliveries (status)"))

        if not insp.has_table("customer_communication_preferences"):
            conn.execute(
                text(
                    """
                    CREATE TABLE customer_communication_preferences (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        customer_id VARCHAR(36) NOT NULL,
                        channel VARCHAR(32) NOT NULL,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        contact_reference VARCHAR(255),
                        preferred INTEGER NOT NULL DEFAULT 0,
                        quiet_hours_start VARCHAR(8),
                        quiet_hours_end VARCHAR(8),
                        timezone_name VARCHAR(64),
                        notes TEXT,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(customer_id) REFERENCES customers (id)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_ccpref_customer ON customer_communication_preferences (customer_id)")
            )
            conn.execute(text("CREATE INDEX ix_ccpref_channel ON customer_communication_preferences (channel)"))

        if not insp.has_table("recurring_system_jobs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE recurring_system_jobs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        job_key VARCHAR(96) NOT NULL UNIQUE,
                        job_type VARCHAR(64) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        schedule_type VARCHAR(32) NOT NULL,
                        schedule_expression VARCHAR(255),
                        timezone_name VARCHAR(64),
                        last_run_at DATETIME,
                        next_run_at DATETIME,
                        max_runtime_seconds INTEGER,
                        dry_run_default INTEGER NOT NULL DEFAULT 0,
                        payload_json TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_rsj_next ON recurring_system_jobs (next_run_at)"))
            conn.execute(text("CREATE INDEX ix_rsj_enabled ON recurring_system_jobs (enabled)"))

        if not insp.has_table("recurring_system_job_runs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE recurring_system_job_runs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        recurring_job_id VARCHAR(36) NOT NULL,
                        job_key VARCHAR(96) NOT NULL,
                        trigger_type VARCHAR(24) NOT NULL,
                        status VARCHAR(24) NOT NULL,
                        started_at DATETIME NOT NULL,
                        completed_at DATETIME,
                        dry_run INTEGER NOT NULL DEFAULT 0,
                        triggered_by_user_id VARCHAR(36),
                        result_summary TEXT,
                        result_json TEXT,
                        error_json TEXT,
                        created_count INTEGER,
                        updated_count INTEGER,
                        skipped_count INTEGER,
                        failed_count INTEGER,
                        idempotency_key VARCHAR(128),
                        FOREIGN KEY(recurring_job_id) REFERENCES recurring_system_jobs (id),
                        FOREIGN KEY(triggered_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_rsjr_job ON recurring_system_job_runs (recurring_job_id)"))
            conn.execute(text("CREATE INDEX ix_rsjr_key ON recurring_system_job_runs (job_key)"))
            conn.execute(text("CREATE INDEX ix_rsjr_status ON recurring_system_job_runs (status)"))
            conn.execute(text("CREATE INDEX ix_rsjr_started ON recurring_system_job_runs (started_at)"))

        if not insp.has_table("internal_access_groups"):
            conn.execute(
                text(
                    """
                    CREATE TABLE internal_access_groups (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        code VARCHAR(64) NOT NULL UNIQUE,
                        group_type VARCHAR(64) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        description TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_iag_type ON internal_access_groups (group_type)"))

        if not insp.has_table("internal_access_group_memberships"):
            conn.execute(
                text(
                    """
                    CREATE TABLE internal_access_group_memberships (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        group_id VARCHAR(36) NOT NULL,
                        user_id VARCHAR(36) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        joined_at DATETIME NOT NULL,
                        left_at DATETIME,
                        notes TEXT,
                        FOREIGN KEY(group_id) REFERENCES internal_access_groups (id),
                        FOREIGN KEY(user_id) REFERENCES users (id),
                        UNIQUE (group_id, user_id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_iagm_group ON internal_access_group_memberships (group_id)"))
            conn.execute(text("CREATE INDEX ix_iagm_user ON internal_access_group_memberships (user_id)"))

        if not insp.has_table("group_permission_grants"):
            conn.execute(
                text(
                    """
                    CREATE TABLE group_permission_grants (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        group_id VARCHAR(36) NOT NULL,
                        permission_key VARCHAR(64) NOT NULL,
                        effect VARCHAR(16) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        expires_at DATETIME,
                        FOREIGN KEY(group_id) REFERENCES internal_access_groups (id),
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id),
                        UNIQUE (group_id, permission_key)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_gpg_group ON group_permission_grants (group_id)"))
            conn.execute(text("CREATE INDEX ix_gpg_key ON group_permission_grants (permission_key)"))

        if not insp.has_table("group_entity_accesses"):
            conn.execute(
                text(
                    """
                    CREATE TABLE group_entity_accesses (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        group_id VARCHAR(36) NOT NULL,
                        entity_type VARCHAR(64) NOT NULL,
                        entity_id VARCHAR(36) NOT NULL,
                        access_scope VARCHAR(32) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(group_id) REFERENCES internal_access_groups (id),
                        UNIQUE (group_id, entity_type, entity_id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_gea_group ON group_entity_accesses (group_id)"))
            conn.execute(text("CREATE INDEX ix_gea_entity ON group_entity_accesses (entity_type, entity_id)"))

        if not insp.has_table("customer_access_groups"):
            conn.execute(
                text(
                    """
                    CREATE TABLE customer_access_groups (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        customer_id VARCHAR(36) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        group_type VARCHAR(64) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(customer_id) REFERENCES customers (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_cag_customer ON customer_access_groups (customer_id)"))

        if not insp.has_table("customer_access_group_memberships"):
            conn.execute(
                text(
                    """
                    CREATE TABLE customer_access_group_memberships (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        customer_access_group_id VARCHAR(36) NOT NULL,
                        portal_login_email VARCHAR(255) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        joined_at DATETIME NOT NULL,
                        notes TEXT,
                        FOREIGN KEY(customer_access_group_id) REFERENCES customer_access_groups (id),
                        UNIQUE (customer_access_group_id, portal_login_email)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_cagm_email ON customer_access_group_memberships (portal_login_email)"))

        if not insp.has_table("customer_group_entity_accesses"):
            conn.execute(
                text(
                    """
                    CREATE TABLE customer_group_entity_accesses (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        customer_access_group_id VARCHAR(36) NOT NULL,
                        entity_type VARCHAR(64) NOT NULL,
                        entity_id VARCHAR(36) NOT NULL,
                        access_scope VARCHAR(32) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(customer_access_group_id) REFERENCES customer_access_groups (id),
                        UNIQUE (customer_access_group_id, entity_type, entity_id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_cgea_group ON customer_group_entity_accesses (customer_access_group_id)"))
            conn.execute(text("CREATE INDEX ix_cgea_entity ON customer_group_entity_accesses (entity_type, entity_id)"))

        if not insp.has_table("org_access_audit_logs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE org_access_audit_logs (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        actor_user_id VARCHAR(36),
                        action VARCHAR(64) NOT NULL,
                        resource_type VARCHAR(64) NOT NULL,
                        resource_id VARCHAR(36),
                        detail_json TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(actor_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_oaa_action ON org_access_audit_logs (action)"))
            conn.execute(text("CREATE INDEX ix_oaa_resource ON org_access_audit_logs (resource_type, resource_id)"))

        if not insp.has_table("communication_provider_events"):
            conn.execute(
                text(
                    """
                    CREATE TABLE communication_provider_events (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        provider_name VARCHAR(64) NOT NULL,
                        event_type VARCHAR(128) NOT NULL,
                        provider_message_id VARCHAR(255),
                        communication_id VARCHAR(36),
                        delivery_id VARCHAR(36),
                        recipient_address VARCHAR(512),
                        occurred_at DATETIME,
                        received_at DATETIME NOT NULL,
                        status VARCHAR(32) NOT NULL,
                        normalized_status VARCHAR(32),
                        payload_json TEXT NOT NULL,
                        processing_result_json TEXT,
                        processing_status VARCHAR(24) NOT NULL,
                        error_message TEXT,
                        external_event_id VARCHAR(255) UNIQUE,
                        FOREIGN KEY(communication_id) REFERENCES contract_customer_communications (id),
                        FOREIGN KEY(delivery_id) REFERENCES contract_customer_communication_deliveries (id)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_cpe_provider_msg ON communication_provider_events (provider_message_id)")
            )
            conn.execute(text("CREATE INDEX ix_cpe_comm ON communication_provider_events (communication_id)"))
            conn.execute(text("CREATE INDEX ix_cpe_delivery ON communication_provider_events (delivery_id)"))
            conn.execute(text("CREATE INDEX ix_cpe_proc ON communication_provider_events (processing_status)"))

        if not insp.has_table("communication_recipient_suppressions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE communication_recipient_suppressions (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        customer_id VARCHAR(36) NOT NULL,
                        recipient_email_normalized VARCHAR(255) NOT NULL,
                        kind VARCHAR(32) NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        requires_manual_review INTEGER NOT NULL DEFAULT 0,
                        first_seen_at DATETIME NOT NULL,
                        last_seen_at DATETIME NOT NULL,
                        last_provider_event_id VARCHAR(36),
                        notes TEXT,
                        FOREIGN KEY(customer_id) REFERENCES customers (id),
                        FOREIGN KEY(last_provider_event_id) REFERENCES communication_provider_events (id)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX ix_crs_cust_email ON communication_recipient_suppressions (customer_id, recipient_email_normalized)"
                )
            )
            conn.execute(text("CREATE INDEX ix_crs_active ON communication_recipient_suppressions (active)"))

        if not insp.has_table("proposal_acceptance_records"):
            conn.execute(
                text(
                    """
                    CREATE TABLE proposal_acceptance_records (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        proposal_id VARCHAR(36) NOT NULL,
                        contract_id VARCHAR(36) NOT NULL,
                        customer_id VARCHAR(36) NOT NULL,
                        source_proposal_reference VARCHAR(64),
                        acceptance_status VARCHAR(32) NOT NULL,
                        acceptance_type VARCHAR(32) NOT NULL,
                        initiated_at DATETIME NOT NULL,
                        completed_at DATETIME,
                        accepted_by_contact VARCHAR(255),
                        accepted_by_customer_user_id VARCHAR(36),
                        acceptance_ip VARCHAR(64),
                        acceptance_user_agent VARCHAR(512),
                        acceptance_channel VARCHAR(32) NOT NULL,
                        acceptance_notes TEXT,
                        signed_name VARCHAR(255),
                        signed_title VARCHAR(255),
                        signed_email VARCHAR(255),
                        evidence_json TEXT,
                        immutable_hash VARCHAR(64),
                        acceptance_evidence_type VARCHAR(32) NOT NULL DEFAULT 'in_product_acceptance',
                        provider_name VARCHAR(64),
                        provider_envelope_id VARCHAR(128),
                        provider_session_id VARCHAR(128),
                        provider_status VARCHAR(32),
                        provider_completed_at DATETIME,
                        provider_payload_json TEXT,
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        amendment_id VARCHAR(36),
                        FOREIGN KEY(proposal_id) REFERENCES contract_repricing_proposals (id) ON DELETE CASCADE,
                        FOREIGN KEY(contract_id) REFERENCES contracts (id),
                        FOREIGN KEY(customer_id) REFERENCES customers (id),
                        FOREIGN KEY(accepted_by_customer_user_id) REFERENCES users (id),
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id),
                        FOREIGN KEY(amendment_id) REFERENCES contract_amendments (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_par_proposal ON proposal_acceptance_records (proposal_id)"))
            conn.execute(text("CREATE INDEX ix_par_contract ON proposal_acceptance_records (contract_id)"))
            conn.execute(text("CREATE INDEX ix_par_status ON proposal_acceptance_records (acceptance_status)"))
            conn.execute(text("CREATE INDEX ix_par_hash ON proposal_acceptance_records (immutable_hash)"))
            conn.execute(text("CREATE INDEX ix_par_evidence_type ON proposal_acceptance_records (acceptance_evidence_type)"))
            conn.execute(text("CREATE INDEX ix_par_provider_env ON proposal_acceptance_records (provider_envelope_id)"))

        if insp.has_table("proposal_acceptance_records"):
            par_cols = {c["name"] for c in insp.get_columns("proposal_acceptance_records")}
            for name, ddl in (
                ("acceptance_evidence_type", "VARCHAR(32) NOT NULL DEFAULT 'in_product_acceptance'"),
                ("provider_name", "VARCHAR(64)"),
                ("provider_envelope_id", "VARCHAR(128)"),
                ("provider_session_id", "VARCHAR(128)"),
                ("provider_status", "VARCHAR(32)"),
                ("provider_completed_at", "DATETIME"),
                ("provider_payload_json", "TEXT"),
            ):
                if name not in par_cols:
                    conn.execute(text(f"ALTER TABLE proposal_acceptance_records ADD COLUMN {name} {ddl}"))
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_par_evidence_type ON proposal_acceptance_records (acceptance_evidence_type)")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_par_provider_env ON proposal_acceptance_records (provider_envelope_id)")
            )

        if not insp.has_table("proposal_acceptance_sessions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE proposal_acceptance_sessions (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        proposal_id VARCHAR(36) NOT NULL,
                        acceptance_record_id VARCHAR(36),
                        session_status VARCHAR(32) NOT NULL,
                        token_hash VARCHAR(64) UNIQUE,
                        expires_at DATETIME,
                        created_at DATETIME NOT NULL,
                        created_by_user_id VARCHAR(36),
                        last_accessed_at DATETIME,
                        completed_at DATETIME,
                        metadata_json TEXT,
                        esign_provider_flow INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(proposal_id) REFERENCES contract_repricing_proposals (id) ON DELETE CASCADE,
                        FOREIGN KEY(acceptance_record_id) REFERENCES proposal_acceptance_records (id) ON DELETE SET NULL,
                        FOREIGN KEY(created_by_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_pas_proposal ON proposal_acceptance_sessions (proposal_id)"))
            conn.execute(text("CREATE INDEX ix_pas_record ON proposal_acceptance_sessions (acceptance_record_id)"))
            conn.execute(text("CREATE INDEX ix_pas_status ON proposal_acceptance_sessions (session_status)"))
            conn.execute(text("CREATE INDEX ix_pas_expires ON proposal_acceptance_sessions (expires_at)"))

        if insp.has_table("proposal_acceptance_sessions"):
            pas_cols = {c["name"] for c in insp.get_columns("proposal_acceptance_sessions")}
            if "esign_provider_flow" not in pas_cols:
                conn.execute(
                    text(
                        "ALTER TABLE proposal_acceptance_sessions ADD COLUMN esign_provider_flow INTEGER NOT NULL DEFAULT 0"
                    )
                )

        if insp.has_table("contract_repricing_proposals"):
            crp_cols = {c["name"] for c in insp.get_columns("contract_repricing_proposals")}
            if "formal_acceptance_record_id" not in crp_cols:
                conn.execute(
                    text("ALTER TABLE contract_repricing_proposals ADD COLUMN formal_acceptance_record_id VARCHAR(36)")
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_crp_formal_acceptance ON contract_repricing_proposals (formal_acceptance_record_id)"
                    )
                )

        # §5.12 — customer org hierarchy + portal member contact scopes
        if insp.has_table("customers"):
            cust_cols = {c["name"] for c in insp.get_columns("customers")}
            if "parent_customer_id" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN parent_customer_id VARCHAR(36)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_customers_parent ON customers (parent_customer_id)"))

        if insp.has_table("customer_access_group_memberships"):
            cagm_cols = {c["name"] for c in insp.get_columns("customer_access_group_memberships")}
            if "member_contact_scope" not in cagm_cols:
                conn.execute(
                    text(
                        "ALTER TABLE customer_access_group_memberships ADD COLUMN member_contact_scope VARCHAR(32) DEFAULT 'full'"
                    )
                )

        # §5.13 — nested internal access groups + inheritance
        if insp.has_table("internal_access_groups"):
            iag_cols = {c["name"] for c in insp.get_columns("internal_access_groups")}
            if "parent_group_id" not in iag_cols:
                conn.execute(text("ALTER TABLE internal_access_groups ADD COLUMN parent_group_id VARCHAR(36)"))
            if "inherit_parent_grants" not in iag_cols:
                conn.execute(
                    text("ALTER TABLE internal_access_groups ADD COLUMN inherit_parent_grants INTEGER NOT NULL DEFAULT 1")
                )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_iag_parent ON internal_access_groups (parent_group_id)")
            )

        if not insp.has_table("break_glass_override_audits"):
            conn.execute(
                text(
                    """
                    CREATE TABLE break_glass_override_audits (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        actor_user_id VARCHAR(36),
                        override_kind VARCHAR(64) NOT NULL,
                        target_type VARCHAR(64) NOT NULL,
                        target_id VARCHAR(36) NOT NULL,
                        reason TEXT NOT NULL,
                        metadata_json TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(actor_user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_bga_actor ON break_glass_override_audits (actor_user_id)"))
            conn.execute(text("CREATE INDEX ix_bga_kind ON break_glass_override_audits (override_kind)"))
            conn.execute(text("CREATE INDEX ix_bga_target ON break_glass_override_audits (target_type, target_id)"))

        # §5.18 — holiday calendar external feed metadata (admin import from URL)
        if insp.has_table("holiday_calendars"):
            hcols = {c["name"] for c in insp.get_columns("holiday_calendars")}
            for col, ddl in (
                ("external_feed_url", "TEXT"),
                ("external_feed_format", "VARCHAR(16) NOT NULL DEFAULT 'ics'"),
                ("last_feed_import_at", "DATETIME"),
                ("last_feed_import_status", "VARCHAR(32)"),
                ("last_feed_import_detail", "TEXT"),
            ):
                if col not in hcols:
                    conn.execute(text(f"ALTER TABLE holiday_calendars ADD COLUMN {col} {ddl}"))
