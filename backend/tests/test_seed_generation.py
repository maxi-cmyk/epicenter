from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backend" / "scripts" / "generate_supabase_seed.py"


def load_generator():
    spec = spec_from_file_location("generate_supabase_seed", SCRIPT)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_seed_counts_and_conservative_identity_gate() -> None:
    seed, counts = load_generator().build_seed()

    assert counts["patients"] == 300
    assert counts["questionnaires"] == 60
    assert counts["documents"] == 9
    assert counts["questionnaires_conflict"] == 54
    assert counts["questionnaires_no_registration"] == 6
    assert "questionnaires_verified" not in counts
    assert "begin;" in seed
    assert "commit;" in seed


def test_seed_does_not_store_raw_identifiers() -> None:
    seed, _ = load_generator().build_seed()

    for raw_identifier in ("S8010946C", "T2221854H", "T1800429G"):
        assert raw_identifier not in seed
