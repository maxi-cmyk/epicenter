-- Run after migrations and both seeds. Any failed invariant aborts the check.
do $$
declare
  actual integer;
begin
  select count(*) into actual from public.patients where deleted_at is null;
  if actual <> 300 then
    raise exception 'expected 300 patients, found %', actual;
  end if;

  select count(*) into actual from public.questionnaire_submissions;
  if actual <> 60 then
    raise exception 'expected 60 questionnaire submissions, found %', actual;
  end if;

  select count(*) into actual from public.medical_document_samples;
  if actual <> 9 then
    raise exception 'expected 9 medical document samples, found %', actual;
  end if;

  select count(*) into actual
  from public.queue_entries
  where clinic_id = 'clinic_harbourfront' and deleted_at is null;
  if actual <> 6 then
    raise exception 'expected 6 seeded queue entries, found %', actual;
  end if;

  select count(*) into actual from public.review_cases where resolved_at is null;
  if actual <> 3 then
    raise exception 'expected 3 unresolved review cases, found %', actual;
  end if;

  select count(*) into actual from public.simulator_snapshots where active;
  if actual <> 3 then
    raise exception 'expected 3 active simulator snapshots, found %', actual;
  end if;

  select count(*) into actual from public.data_import_exceptions
  where reason_code = 'unmatched_patient' and resolution_status = 'unresolved';
  if actual <> 6 then
    raise exception 'expected 6 unmatched questionnaire exceptions, found %', actual;
  end if;

  select count(*) into actual from public.coverage_documents where deleted_at is null;
  if actual <> 2 then
    raise exception 'expected 2 canonical coverage documents, found %', actual;
  end if;

  select count(*) into actual from public.manual_check_confirmations
  where queue_entry_id = 'Q-019';
  if actual <> 1 then
    raise exception 'expected one manual check attestation for Q-019, found %', actual;
  end if;

  select count(*) into actual from public.appointments
  where administrative_urgency and deleted_at is null;
  if actual < 1 then
    raise exception 'expected at least one administrative-urgency appointment';
  end if;

  select count(*) into actual from public.allocation_recommendations
  where status = 'approved' and decided_by_reference is not null;
  if actual < 1 then
    raise exception 'expected at least one human-decided allocation recommendation';
  end if;

  select count(distinct outcome) into actual from public.patient_submissions
  where outcome in ('accepted', 'rejected', 'under_review') and deleted_at is null;
  if actual <> 3 then
    raise exception 'expected seeded accepted, rejected, and under-review outcomes, found %', actual;
  end if;

  select count(*) into actual from public.simulator_runs
  where status = 'completed' and result_payload is not null;
  if actual <> 3 then
    raise exception 'expected 3 completed simulator runs, found %', actual;
  end if;

  select count(*) into actual
  from public.queue_entries
  where readiness_state = 'ready'
    and (
      not staff_confirmed
      or (intake_type = 'booked' and prereg_completed_at is null)
      or not all_required_documents_present
      or not all_documents_valid
      or extraction_status <> 'pass'
      or match_status <> 'clean'
    );
  if actual <> 0 then
    raise exception 'false-ready invariant failed for % queue entries', actual;
  end if;

  select count(*) into actual
  from (
    select appointment_id
    from public.queue_entries
    where appointment_id is not null and deleted_at is null
    group by appointment_id
    having count(*) > 1
  ) duplicates;
  if actual <> 0 then
    raise exception 'one-ticket invariant failed for % appointments', actual;
  end if;

  if has_table_privilege('anon', 'public.queue_entries', 'select')
    or has_table_privilege('authenticated', 'public.queue_entries', 'select') then
    raise exception 'queue_entries is exposed to a browser database role';
  end if;

  select count(*) into actual
  from unnest(array[
    'data_import_exceptions', 'registration_validations', 'coverage_documents',
    'eligibility_rules', 'eligibility_matches', 'coverage_reuse_decisions',
    'patient_submissions', 'patient_notifications'
  ]) as expected(table_name)
  join pg_class relation on relation.relname = expected.table_name
  join pg_namespace schema_name on schema_name.oid = relation.relnamespace
  where schema_name.nspname = 'public' and not relation.relrowsecurity;
  if actual <> 0 then
    raise exception 'RLS is disabled on % Task 2 tables', actual;
  end if;

  select count(*) into actual
  from information_schema.role_table_grants
  where table_schema = 'public'
    and table_name in (
      'registration_validations', 'coverage_documents', 'eligibility_rules',
      'eligibility_matches', 'coverage_reuse_decisions', 'patient_submissions',
      'patient_notifications', 'audit_log', 'operational_events'
    )
    and grantee in ('anon', 'authenticated');
  if actual <> 0 then
    raise exception 'browser database roles retain % direct Task 2 table grants', actual;
  end if;
end;
$$;

select
  (select count(*) from public.patients where deleted_at is null) as patients,
  (select count(*) from public.questionnaire_submissions) as questionnaires,
  (select count(*) from public.medical_document_samples) as documents,
  (select count(*) from public.appointments where deleted_at is null) as appointments,
  (select count(*) from public.queue_entries where deleted_at is null) as tickets,
  (select count(*) from public.review_cases where resolved_at is null) as open_reviews,
  (select count(*) from public.data_import_exceptions where resolution_status = 'unresolved') as import_exceptions,
  (select count(*) from public.coverage_documents where deleted_at is null) as coverage_documents,
  (select count(*) from public.manual_check_confirmations) as manual_attestations,
  (select count(*) from public.simulator_snapshots where active) as simulator_snapshots,
  (select count(*) from public.simulator_runs where status = 'completed') as simulator_runs;
