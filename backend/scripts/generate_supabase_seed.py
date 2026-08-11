"""Generate an idempotent Supabase seed from the supplied synthetic fixtures."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "derived" / "medical_chit_manifest.json"
OUTPUT = ROOT / "supabase" / "seed.sql"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_identifier(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def identifier_hash(value: str) -> str:
    return hashlib.sha256(normalize_identifier(value).encode()).hexdigest()


def mask_identifier(value: str) -> str:
    normalized = normalize_identifier(value)
    return f"{'*' * max(0, len(normalized) - 4)}{normalized[-4:]}"


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date: {value!r}")


def boolean(value: str | None) -> bool | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"yes", "true", "acknowledged", "consented"}:
        return True
    if normalized in {"no", "false", "not acknowledged", "not consented"}:
        return False
    return None


def sql_json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return "$json$" + encoded + "$json$::jsonb"


def build_seed() -> tuple[str, dict[str, int]]:
    registrations = read_csv(RAW / "patient_registration_synthetic.csv")
    patient_by_hash = {identifier_hash(row["NRIC/FIN/Passport Number"]): row for row in registrations}

    patient_payloads = []
    for index, row in enumerate(registrations, start=1):
        patient_payloads.append(
            {
                "source_record_key": f"registration:{index:04d}",
                "identifier_hash": identifier_hash(row["NRIC/FIN/Passport Number"]),
                "identifier_masked": mask_identifier(row["NRIC/FIN/Passport Number"]),
                "full_name": row["Full Name"],
                "sex": row["Sex"] or None,
                "nationality": row["Nationality"] or None,
                "date_of_birth": parse_date(row["Date of Birth (DD/MM/YY)"]),
                "address": row["Address"] or None,
                "postal_code": row["Postal Code"] or None,
                "contact_home": row["Contact - Home"] or None,
                "contact_office": row["Contact - Office"] or None,
                "contact_mobile": row["Contact - Mobile"] or None,
                "email": row["Email"] or None,
                "drug_allergy": row["Drug Allergy"] or None,
            }
        )

    questionnaires = []
    questionnaire_sources = (
        ("general_health", RAW / "general_health_questionnaire_mock_patients.csv"),
        ("occupational_health", RAW / "occupational_health_questionnaire_mock_patients.csv"),
    )
    status_counts: dict[str, int] = {}
    for questionnaire_type, path in questionnaire_sources:
        for index, row in enumerate(read_csv(path), start=1):
            subject_hash = identifier_hash(row["ID Number"])
            candidate = patient_by_hash.get(subject_hash)
            name_match = bool(candidate) and candidate["Full Name"].strip().casefold() == row["Name"].strip().casefold()
            dob_match = bool(candidate) and parse_date(candidate["Date of Birth (DD/MM/YY)"]) == parse_date(
                row["Date of Birth"]
            )
            email_match = (
                bool(candidate) and candidate["Email"].strip().casefold() == row["Email Address"].strip().casefold()
            )
            if not candidate:
                status = "no_registration"
            elif name_match and dob_match:
                status = "verified"
            else:
                status = "conflict"
            status_counts[status] = status_counts.get(status, 0) + 1
            response_payload = {key: value for key, value in row.items() if key != "ID Number"}
            questionnaires.append(
                {
                    "source_record_key": f"{questionnaire_type}:{index:04d}",
                    "questionnaire_type": questionnaire_type,
                    "subject_identifier_hash": subject_hash,
                    "subject_identifier_masked": mask_identifier(row["ID Number"]),
                    "subject_name": row["Name"],
                    "subject_date_of_birth": parse_date(row["Date of Birth"]),
                    "subject_email": row["Email Address"] or None,
                    "candidate_identifier_hash": subject_hash if candidate else None,
                    "verified_identifier_hash": subject_hash if status == "verified" else None,
                    "verification_status": status,
                    "verification_evidence": {
                        "identifier_match": bool(candidate),
                        "name_match": name_match,
                        "date_of_birth_match": dob_match,
                        "email_match": email_match,
                    },
                    "acknowledged": boolean(row.get("Acknowledged Declaration")),
                    "consent_to_disclose": boolean(row.get("Consent to Disclose to Employer/Insurer")),
                    "signed_on": parse_date(row.get("Date Signed")),
                    "response_payload": response_payload,
                }
            )

    documents = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for document in documents:
        identifier = document.pop("subject_identifier", None)
        document["subject_identifier_hash"] = identifier_hash(identifier) if identifier else None
        document["subject_identifier_masked"] = mask_identifier(identifier) if identifier else None

    lines = [
        "-- Generated by backend/scripts/generate_supabase_seed.py.",
        "-- All records are synthetic. Re-running this file is idempotent.",
        "begin;",
        "",
        "with source as (",
        "  select * from jsonb_to_recordset(" + sql_json(patient_payloads) + ") as x(",
        "    source_record_key text, identifier_hash text, identifier_masked text, full_name text,",
        "    sex text, nationality text, date_of_birth date, address text, postal_code text,",
        "    contact_home text, contact_office text, contact_mobile text, email text, drug_allergy text",
        "  )",
        ")",
        "insert into public.patients (source_record_key, identifier_hash, identifier_masked, full_name, sex, nationality, date_of_birth, address, postal_code, contact_home, contact_office, contact_mobile, email, drug_allergy)",
        "select source_record_key, identifier_hash, identifier_masked, full_name, sex, nationality, date_of_birth, address, postal_code, contact_home, contact_office, contact_mobile, email, drug_allergy from source",
        "on conflict (source_record_key) do update set",
        "  identifier_hash = excluded.identifier_hash, identifier_masked = excluded.identifier_masked,",
        "  full_name = excluded.full_name, sex = excluded.sex, nationality = excluded.nationality,",
        "  date_of_birth = excluded.date_of_birth, address = excluded.address, postal_code = excluded.postal_code,",
        "  contact_home = excluded.contact_home, contact_office = excluded.contact_office,",
        "  contact_mobile = excluded.contact_mobile, email = excluded.email, drug_allergy = excluded.drug_allergy;",
        "",
        "with source as (",
        "  select * from jsonb_to_recordset(" + sql_json(questionnaires) + ") as x(",
        "    source_record_key text, questionnaire_type text, subject_identifier_hash text,",
        "    subject_identifier_masked text, subject_name text, subject_date_of_birth date, subject_email text,",
        "    candidate_identifier_hash text, verified_identifier_hash text, verification_status text,",
        "    verification_evidence jsonb, acknowledged boolean, consent_to_disclose boolean, signed_on date, response_payload jsonb",
        "  )",
        ")",
        "insert into public.questionnaire_submissions (source_record_key, questionnaire_type, subject_identifier_hash, subject_identifier_masked, subject_name, subject_date_of_birth, subject_email, patient_id, candidate_patient_id, verification_status, verification_evidence, acknowledged, consent_to_disclose, signed_on, response_payload)",
        "select s.source_record_key, s.questionnaire_type, s.subject_identifier_hash, s.subject_identifier_masked, s.subject_name, s.subject_date_of_birth, s.subject_email, verified.id, candidate.id, s.verification_status, s.verification_evidence, s.acknowledged, s.consent_to_disclose, s.signed_on, s.response_payload",
        "from source s",
        "left join public.patients candidate on candidate.identifier_hash = s.candidate_identifier_hash",
        "left join public.patients verified on verified.identifier_hash = s.verified_identifier_hash",
        "on conflict (source_record_key) do update set",
        "  questionnaire_type = excluded.questionnaire_type, subject_identifier_hash = excluded.subject_identifier_hash,",
        "  subject_identifier_masked = excluded.subject_identifier_masked, subject_name = excluded.subject_name,",
        "  subject_date_of_birth = excluded.subject_date_of_birth, subject_email = excluded.subject_email,",
        "  patient_id = excluded.patient_id, candidate_patient_id = excluded.candidate_patient_id,",
        "  verification_status = excluded.verification_status, verification_evidence = excluded.verification_evidence,",
        "  acknowledged = excluded.acknowledged, consent_to_disclose = excluded.consent_to_disclose,",
        "  signed_on = excluded.signed_on, response_payload = excluded.response_payload;",
        "",
        "with source as (",
        "  select * from jsonb_to_recordset(" + sql_json(documents) + ") as x(",
        "    source_record_key text, issuer_code text, issuer_name text, document_kind text, subject_name text,",
        "    subject_identifier_hash text, subject_identifier_masked text, issued_on date, expires_on date,",
        "    appointment_at timestamptz, requirements jsonb, administrative_facts jsonb,",
        "    automation_disposition text, review_reason text",
        "  )",
        ")",
        "insert into public.medical_document_samples (source_record_key, issuer_code, issuer_name, document_kind, subject_name, subject_identifier_hash, subject_identifier_masked, patient_id, issued_on, expires_on, appointment_at, requirements, administrative_facts, automation_disposition, review_reason)",
        "select s.source_record_key, s.issuer_code, s.issuer_name, s.document_kind, s.subject_name, s.subject_identifier_hash, s.subject_identifier_masked, p.id, s.issued_on, s.expires_on, s.appointment_at, s.requirements, s.administrative_facts, s.automation_disposition, s.review_reason",
        "from source s left join public.patients p on p.identifier_hash = s.subject_identifier_hash",
        "on conflict (source_record_key) do update set",
        "  issuer_code = excluded.issuer_code, issuer_name = excluded.issuer_name, document_kind = excluded.document_kind,",
        "  subject_name = excluded.subject_name, subject_identifier_hash = excluded.subject_identifier_hash,",
        "  subject_identifier_masked = excluded.subject_identifier_masked, patient_id = excluded.patient_id,",
        "  issued_on = excluded.issued_on, expires_on = excluded.expires_on, appointment_at = excluded.appointment_at,",
        "  requirements = excluded.requirements, administrative_facts = excluded.administrative_facts,",
        "  automation_disposition = excluded.automation_disposition, review_reason = excluded.review_reason;",
        "",
        "commit;",
        "",
    ]
    return "\n".join(lines), {
        "patients": len(patient_payloads),
        "questionnaires": len(questionnaires),
        "documents": len(documents),
        **{f"questionnaires_{key}": value for key, value in status_counts.items()},
    }


if __name__ == "__main__":
    seed, counts = build_seed()
    OUTPUT.write_text(seed, encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), **counts}, indent=2))
