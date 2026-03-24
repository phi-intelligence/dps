# PostgreSQL DDL snippets

PHI-DPS defaults to SQLite in development (`PHI_DPS_DATABASE_URL=sqlite:///...`). SQLite picks up new columns via `backend/app/db/sqlite_migrations.py` on API startup.

For **PostgreSQL** (or other servers) managed outside `create_all`, apply scripts in order when the model adds columns that are not yet in your database.

| Script | Purpose |
|--------|---------|
| `001_holiday_calendar_feed_columns.sql` | §5.18 holiday calendar external feed + import audit columns |

After applying, restart the API and verify `GET /labour/calendars` returns the new fields.
