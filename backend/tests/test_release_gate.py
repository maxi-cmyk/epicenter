"""Static release checks that protect the deployment contract."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"


def test_migration_versions_are_unique() -> None:
    versions: dict[str, list[str]] = {}
    for migration in MIGRATIONS.glob("*.sql"):
        version = migration.name.split("_", 1)[0]
        versions.setdefault(version, []).append(migration.name)

    duplicates = {version: names for version, names in versions.items() if len(names) > 1}
    assert duplicates == {}, f"Duplicate Supabase migration versions: {duplicates}"


def test_initial_schema_snapshot_matches_initial_migration() -> None:
    snapshot = (ROOT / "backend" / "persistence" / "schema.sql").read_text()
    initial = (MIGRATIONS / "20260811132842_initial_clinic_data.sql").read_text()

    snapshot_body = re.sub(r"\A(?:--.*\n|\n){4}", "", snapshot)
    assert snapshot_body == initial


def test_configured_seed_files_exist() -> None:
    config = tomllib.loads((ROOT / "supabase" / "config.toml").read_text())
    seed_paths = config["db"]["seed"]["sql_paths"]
    assert seed_paths
    for seed_path in seed_paths:
        assert (ROOT / "supabase" / seed_path.removeprefix("./")).is_file()


def test_each_frontend_has_an_independent_deployment_contract() -> None:
    for app_name in ("patient", "nurse"):
        app_dir = ROOT / "frontend" / app_name
        assert (app_dir / "vercel.json").is_file()
        env_example = (app_dir / ".env.example").read_text()
        assert "NEXT_PUBLIC_API_BASE_URL=" in env_example
        assert "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=" in env_example
        assert "SECRET_KEY" not in env_example
        assert "OPENAI_API_KEY" not in env_example


def test_railway_api_and_worker_commands_are_declared() -> None:
    railway = tomllib.loads((ROOT / "backend" / "railway.toml").read_text())
    assert railway["deploy"]["healthcheckPath"] == "/healthz"
    assert "uvicorn app.main:app" in railway["deploy"]["startCommand"]

    procfile = (ROOT / "backend" / "Procfile").read_text()
    assert "web: uvicorn app.main:app" in procfile
    assert "worker: python -m worker" in procfile
