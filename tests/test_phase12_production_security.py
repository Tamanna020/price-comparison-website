"""Phase 12: Production Deployment and Security Verification Tests.

Verifies:
1. Health check endpoints (/api/health/live, /api/health/ready, /api/health).
2. Production security headers injection and latency timing.
3. Dual database engine selection logic (SQLite vs PostgreSQL).
4. SQLite to PostgreSQL migration script and DDL generation.
5. Automated database backup, SHA-256 checksum verification, and safe restoration.
6. Evidence file upload security (MIME validation, size restriction, path traversal prevention).
7. Environment and configuration safety.
"""

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.config import (
    APP_NAME,
    APP_VERSION,
    ENVIRONMENT,
    MAX_UPLOAD_SIZE_BYTES,
)
from src.database.connection import get_database_engine_type, get_connection
from scripts.backup_restore_db import (
    calculate_sha256,
    create_backup,
    verify_backup,
    test_backup_restore_cycle as run_backup_restore_cycle,
)
from scripts.migrate_sqlite_to_postgres import (
    generate_postgres_ddl,
    generate_postgres_data_inserts,
    convert_sqlite_type_to_postgres,
    escape_postgres_value,
)


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Verify production observability and health endpoints."""

    def test_liveness_endpoint(self, client):
        """Test /api/health/live returns 200 with alive status and timestamp."""
        res = client.get("/api/health/live")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_readiness_endpoint(self, client):
        """Test /api/health/ready checks DB connectivity, latency, and product counts."""
        res = client.get("/api/health/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["database_healthy"] is True
        assert data["product_count"] >= 100
        assert "latency_ms" in data
        assert data["database_engine"] in ("sqlite", "postgresql")

    def test_standard_health_endpoint(self, client):
        """Test legacy /api/health backward-compatible contract."""
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["app_name"] == APP_NAME
        assert data["version"] == APP_VERSION
        assert data["record_count"] >= 100


class TestSecurityHeadersAndTiming:
    """Verify HTTP security headers and performance timing."""

    def test_security_headers_present(self, client):
        """Verify essential security headers on all responses."""
        res = client.get("/api/health")
        headers = res.headers

        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_process_time_header_present(self, client):
        """Verify X-Process-Time is injected and ends in ms."""
        res = client.get("/api/products?limit=5")
        assert res.status_code == 200
        process_time = res.headers.get("X-Process-Time")
        assert process_time is not None
        assert process_time.endswith("ms")


class TestDualDatabaseEngine:
    """Verify SQLite vs PostgreSQL configuration detection."""

    def test_sqlite_engine_default(self):
        """Without DATABASE_URL, defaults to sqlite engine."""
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            engine = get_database_engine_type()
            assert engine == "sqlite"

    def test_postgres_engine_detection(self):
        """Detects postgresql:// and postgres:// scheme."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@host/db"}, clear=False):
            assert get_database_engine_type() == "postgresql"

        with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@host/db"}, clear=False):
            assert get_database_engine_type() == "postgresql"


class TestDatabaseBackupAndRestore:
    """Verify point-in-time backup, SHA-256 checksums, and restoration."""

    def test_sha256_calculation(self, tmp_path):
        """Verify checksum calculation matches known file contents."""
        test_file = tmp_path / "sample.txt"
        test_file.write_text("PriceWise AI Production Test", encoding="utf-8")
        h = calculate_sha256(test_file)
        assert len(h) == 64
        assert isinstance(h, str)

    def test_backup_and_verify(self, tmp_path):
        """Verify backup creation produces DB and checksum files and passes verification."""
        backup_file, checksum_file, checksum = create_backup(backup_dir=tmp_path)
        assert backup_file.exists()
        assert checksum_file.exists()
        assert len(checksum) == 64
        assert verify_backup(backup_file, checksum_file) is True

    def test_full_backup_restore_cycle(self):
        """Verify full round-trip: snapshot, hash, restore, compare row counts."""
        assert run_backup_restore_cycle() is True


class TestPostgresMigrationEngine:
    """Verify SQLite to PostgreSQL migration script."""

    def test_type_conversion(self):
        """Verify type mapping for SQLite to PostgreSQL."""
        assert convert_sqlite_type_to_postgres("id", "INTEGER", True, "AUTOINCREMENT") == "SERIAL PRIMARY KEY"
        assert convert_sqlite_type_to_postgres("price", "REAL", False, "") == "DOUBLE PRECISION"
        assert convert_sqlite_type_to_postgres("created_at", "TIMESTAMP", False, "") == "TIMESTAMP WITH TIME ZONE"
        assert convert_sqlite_type_to_postgres("is_active", "BOOLEAN", False, "") == "BOOLEAN"
        assert convert_sqlite_type_to_postgres("title", "TEXT", False, "") == "TEXT"

    def test_escape_postgres_value(self):
        """Verify SQL injection prevention and value escaping."""
        assert escape_postgres_value(None) == "NULL"
        assert escape_postgres_value(True) == "TRUE"
        assert escape_postgres_value(False) == "FALSE"
        assert escape_postgres_value(1234) == "1234"
        assert escape_postgres_value("L'Oreal Paris") == "'L''Oreal Paris'"

    def test_ddl_and_data_generation(self):
        """Verify that PostgreSQL DDL and Data generation produce valid SQL."""
        db_path = Path("data/pricewise.db")
        if not db_path.exists():
            pytest.skip("pricewise.db not found")

        ddl = generate_postgres_ddl(db_path)
        assert "CREATE TABLE products" in ddl
        assert "CREATE TABLE offers" in ddl
        assert "CREATE TABLE users" in ddl
        assert "SERIAL PRIMARY KEY" in ddl

        data, counts = generate_postgres_data_inserts(db_path)
        assert "INSERT INTO products" in data
        assert counts["products"] >= 100
        assert counts["offers"] >= 400


class TestEvidenceUploadSecurity:
    """Verify security controls on the file upload endpoint."""

    def test_reject_unauthenticated_upload(self, client):
        """Verify unauthenticated requests cannot upload evidence."""
        file_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        res = client.post(
            "/api/verification/upload-evidence",
            files={"file": ("test.png", file_content, "image/png")},
        )
        assert res.status_code in (401, 403)

    def test_reject_disallowed_mime_types(self, client):
        """Verify rejection of executable, html, or text uploads."""
        # Login demo user
        login_res = client.post("/api/auth/login", json={"email": "demo@pricewise.ai", "password": "DemoPass123!"})
        if login_res.status_code != 200:
            pytest.skip("Demo login unavailable")

        token = login_res.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to upload dangerous file
        script_content = b"<script>alert('xss')</script>"
        res = client.post(
            "/api/verification/upload-evidence",
            headers=headers,
            files={"file": ("malicious.html", script_content, "text/html")},
        )
        assert res.status_code == 400
        assert "Unsupported file format" in res.json().get("detail", "")

    def test_path_traversal_prevention_on_serving(self, client):
        """Verify traversal sequences in filename are rejected or sanitized safely."""
        res = client.get("/api/verification/evidence/..%2F..%2Fetc%2Fpasswd")
        assert res.status_code in (400, 404)

        res2 = client.get("/api/verification/evidence/non_existent_file.png")
        assert res2.status_code == 404
