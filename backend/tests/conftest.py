import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Allow `pytest` from backend/ or repo root: package is `backend.app`.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


DB_PATH = Path(__file__).resolve().parent / "test.db"
if DB_PATH.exists():
    DB_PATH.unlink()

_DOC_ROOT = Path(__file__).resolve().parent / "phi_dps_doc_store_test"
_DOC_ROOT.mkdir(parents=True, exist_ok=True)

# IMPORTANT: set env vars before importing the app, so settings pick up test DB.
os.environ["PHI_DPS_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["PHI_DPS_DEV_BOOTSTRAP"] = "1"
os.environ["PHI_DPS_SECRET_KEY"] = "test-secret-key"
os.environ["PHI_DPS_DOCUMENT_STORAGE_ROOT"] = str(_DOC_ROOT)


@pytest.fixture(scope="session")
def client():
    from backend.app.main import app

    with TestClient(app) as c:
        yield c

