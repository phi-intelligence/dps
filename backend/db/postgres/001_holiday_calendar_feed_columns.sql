-- §5.18 — Apply when using PostgreSQL (SQLite uses sqlite_migrations.py on startup).
-- Run once per environment if holiday_calendars existed before feed columns were added.

ALTER TABLE holiday_calendars ADD COLUMN IF NOT EXISTS external_feed_url TEXT;
ALTER TABLE holiday_calendars ADD COLUMN IF NOT EXISTS external_feed_format VARCHAR(16) NOT NULL DEFAULT 'ics';
ALTER TABLE holiday_calendars ADD COLUMN IF NOT EXISTS last_feed_import_at TIMESTAMPTZ;
ALTER TABLE holiday_calendars ADD COLUMN IF NOT EXISTS last_feed_import_status VARCHAR(32);
ALTER TABLE holiday_calendars ADD COLUMN IF NOT EXISTS last_feed_import_detail TEXT;
