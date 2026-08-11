-- SQL Editor snapshot of:
-- supabase/migrations/20260811132842_initial_clinic_data.sql
-- Keep this file byte-for-byte aligned with the migration statements below.

create table public.patients (
  id bigint generated always as identity primary key,
  source_record_key text not null unique,
  identifier_hash text not null unique
    check (identifier_hash ~ '^[0-9a-f]{64}$'),
  identifier_masked text not null,
  full_name text not null,
  sex text,
  nationality text,
  date_of_birth date,
  address text,
  postal_code text,
  contact_home text,
  contact_office text,
  contact_mobile text,
  email text,
  drug_allergy text,
  is_synthetic boolean not null default true,
  imported_at timestamptz not null default now()
);

create table public.questionnaire_submissions (
  id bigint generated always as identity primary key,
  source_record_key text not null unique,
  questionnaire_type text not null
    check (questionnaire_type in ('general_health', 'occupational_health')),
  subject_identifier_hash text not null
    check (subject_identifier_hash ~ '^[0-9a-f]{64}$'),
  subject_identifier_masked text not null,
  subject_name text not null,
  subject_date_of_birth date,
  subject_email text,
  patient_id bigint references public.patients(id) on delete set null,
  candidate_patient_id bigint references public.patients(id) on delete set null,
  verification_status text not null
    check (verification_status in ('verified', 'conflict', 'no_registration', 'ambiguous')),
  verification_evidence jsonb not null default '{}'::jsonb,
  acknowledged boolean,
  consent_to_disclose boolean,
  signed_on date,
  response_payload jsonb not null default '{}'::jsonb,
  is_synthetic boolean not null default true,
  imported_at timestamptz not null default now(),
  check (patient_id is null or verification_status = 'verified')
);

create index questionnaire_submissions_patient_id_idx
  on public.questionnaire_submissions (patient_id);
create index questionnaire_submissions_candidate_patient_id_idx
  on public.questionnaire_submissions (candidate_patient_id);
create index questionnaire_submissions_verification_status_idx
  on public.questionnaire_submissions (verification_status);

create table public.medical_document_samples (
  id bigint generated always as identity primary key,
  source_record_key text not null unique,
  issuer_code text not null,
  issuer_name text not null,
  document_kind text not null,
  subject_name text,
  subject_identifier_hash text
    check (subject_identifier_hash is null or subject_identifier_hash ~ '^[0-9a-f]{64}$'),
  subject_identifier_masked text,
  patient_id bigint references public.patients(id) on delete set null,
  issued_on date,
  expires_on date,
  appointment_at timestamptz,
  requirements jsonb not null default '[]'::jsonb,
  administrative_facts jsonb not null default '{}'::jsonb,
  automation_disposition text not null
    check (automation_disposition in ('confirm', 'staff_review')),
  review_reason text,
  is_synthetic boolean not null default true,
  imported_at timestamptz not null default now()
);

create index medical_document_samples_patient_id_idx
  on public.medical_document_samples (patient_id);
create index medical_document_samples_disposition_idx
  on public.medical_document_samples (automation_disposition);

alter table public.patients enable row level security;
alter table public.questionnaire_submissions enable row level security;
alter table public.medical_document_samples enable row level security;

revoke all on table public.patients from anon, authenticated;
revoke all on table public.questionnaire_submissions from anon, authenticated;
revoke all on table public.medical_document_samples from anon, authenticated;
revoke all on sequence public.patients_id_seq from anon, authenticated;
revoke all on sequence public.questionnaire_submissions_id_seq from anon, authenticated;
revoke all on sequence public.medical_document_samples_id_seq from anon, authenticated;

grant select, insert, update, delete on table public.patients to service_role;
grant select, insert, update, delete on table public.questionnaire_submissions to service_role;
grant select, insert, update, delete on table public.medical_document_samples to service_role;
grant usage, select on sequence public.patients_id_seq to service_role;
grant usage, select on sequence public.questionnaire_submissions_id_seq to service_role;
grant usage, select on sequence public.medical_document_samples_id_seq to service_role;

comment on table public.patients is
  'Synthetic registration fixtures. Government identifiers are stored only as deterministic hashes plus masked display values.';
comment on table public.questionnaire_submissions is
  'Synthetic questionnaire fixtures. Only verified identity matches populate patient_id; conflicts remain review work.';
comment on table public.medical_document_samples is
  'Synthetic medical chit facts extracted from the supplied fictional sample letters.';
