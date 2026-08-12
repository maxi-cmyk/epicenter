begin;

-- First-time signup coverage is patient-scoped (no appointment yet).
create or replace function public.epicenter_submit_onboarding_coverage(
  p_patient_id bigint,
  p_file_name text,
  p_clinic_id text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  document_row public.coverage_documents%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('onboarding_coverage:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'onboarding_coverage' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;

  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;
  if nullif(trim(p_file_name), '') is null then
    raise exception 'replacement_document_required' using errcode = 'PT422';
  end if;
  if not exists (
    select 1 from public.patients where id = p_patient_id and deleted_at is null
  ) then
    raise exception 'patient_not_found' using errcode = 'PT404';
  end if;

  insert into public.coverage_documents (
    id, clinic_id, patient_id, appointment_id, file_reference, document_type,
    patient_match_status, readiness_status, readiness_reasons, processing_status, review_status
  ) values (
    'DOC-ONB-' || upper(substr(md5(p_idempotency_key), 1, 12)),
    coalesce(nullif(trim(p_clinic_id), ''), 'clinic_harbourfront'),
    p_patient_id,
    null,
    trim(p_file_name),
    'other',
    'needs_review',
    'needs_review',
    '["onboarding_upload"]'::jsonb,
    'processing',
    'pending_review'
  ) returning * into document_row;

  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    document_row.clinic_id, p_actor_reference, p_patient_id, 'submit_onboarding_coverage',
    'coverage_documents', document_row.id,
    jsonb_build_object('file_reference', document_row.file_reference, 'entry_source', 'onboarding')
  );

  existing_response := jsonb_build_object(
    'id', document_row.id,
    'outcome', 'under_review',
    'patient_next_action', 'Coverage saved for your profile. You can book an appointment after onboarding.',
    'processing_reference', document_row.id
  );
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('onboarding_coverage', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

-- Insurance step requires a patient-level onboarding coverage document, not an appointment submission.
create or replace function public.epicenter_advance_onboarding(
  p_clerk_user_id text,
  p_patient_id bigint,
  p_step text,
  p_singpass_authenticated boolean,
  p_insurance_completed boolean,
  p_questionnaire_completed boolean,
  p_singpass_profile jsonb,
  p_appointment_reference text,
  p_actor_reference text,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  existing_response jsonb;
  state_row public.patient_onboarding_states%rowtype;
  appointment_row public.appointments%rowtype;
  was_singpass_authenticated boolean;
  was_insurance_completed boolean;
  was_questionnaire_completed boolean;
  coverage_count integer;
  questionnaire_row public.appointment_questionnaire_responses%rowtype;
begin
  perform pg_advisory_xact_lock(hashtextextended('onboarding_advance:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'onboarding_advance' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;

  if nullif(trim(p_clerk_user_id), '') is null or p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;
  if p_step not in ('singpass', 'insurance', 'questionnaire', 'complete') then
    raise exception 'invalid_onboarding_step' using errcode = 'PT422';
  end if;

  select * into state_row from public.patient_onboarding_states
  where clerk_user_id = p_clerk_user_id for update;
  if not found then
    insert into public.patient_onboarding_states (
      clerk_user_id, patient_id, appointment_reference
    ) values (
      p_clerk_user_id, p_patient_id,
      coalesce(nullif(trim(p_appointment_reference), ''), '')
    ) returning * into state_row;
    select * into state_row from public.patient_onboarding_states
    where clerk_user_id = p_clerk_user_id for update;
  elsif state_row.patient_id <> p_patient_id then
    raise exception 'onboarding_patient_mismatch' using errcode = 'PT409';
  end if;

  was_singpass_authenticated := state_row.singpass_authenticated;
  was_insurance_completed := state_row.insurance_completed;
  was_questionnaire_completed := state_row.questionnaire_completed;

  if p_singpass_authenticated is not null then
    state_row.singpass_authenticated := p_singpass_authenticated;
    if p_singpass_authenticated and p_singpass_profile is not null then
      state_row.singpass_profile := p_singpass_profile;
    end if;
  end if;
  if p_insurance_completed is not null then
    state_row.insurance_completed := p_insurance_completed;
  end if;
  if p_questionnaire_completed is not null then
    state_row.questionnaire_completed := p_questionnaire_completed;
  end if;

  if p_step = 'singpass' then
    if not state_row.singpass_authenticated then
      raise exception 'singpass_required' using errcode = 'PT409';
    end if;
    if was_singpass_authenticated then
      state_row.current_step := 'insurance';
    end if;
  elsif p_step = 'insurance' then
    if not state_row.insurance_completed then
      raise exception 'insurance_required' using errcode = 'PT409';
    end if;
    select count(*) into coverage_count from public.coverage_documents
    where patient_id = p_patient_id
      and appointment_id is null
      and deleted_at is null;
    if coverage_count < 1 then
      raise exception 'coverage_submission_required' using errcode = 'PT409';
    end if;
    if was_insurance_completed or coalesce(p_insurance_completed, false) then
      state_row.current_step := 'questionnaire';
    end if;
  elsif p_step = 'questionnaire' then
    if not state_row.questionnaire_completed then
      raise exception 'questionnaire_required' using errcode = 'PT409';
    end if;
    if nullif(trim(state_row.appointment_reference), '') is not null then
      select * into appointment_row from public.appointments
      where appointment_reference = state_row.appointment_reference
        and patient_id = p_patient_id
        and deleted_at is null;
      if found then
        select * into questionnaire_row from public.appointment_questionnaire_responses
        where appointment_id = appointment_row.id and patient_id = p_patient_id;
      end if;
    end if;
    if questionnaire_row.id is null then
      select r.* into questionnaire_row
      from public.appointment_questionnaire_responses r
      join public.appointments a on a.id = r.appointment_id
      where r.patient_id = p_patient_id
        and r.status = 'submitted'
        and a.deleted_at is null
      order by r.updated_at desc
      limit 1;
    end if;
    if questionnaire_row.id is null or questionnaire_row.status <> 'submitted' then
      raise exception 'questionnaire_submission_required' using errcode = 'PT409';
    end if;
    if was_questionnaire_completed or coalesce(p_questionnaire_completed, false) then
      state_row.current_step := 'complete';
      state_row.completed := true;
    end if;
  elsif p_step = 'complete' then
    if not (
      state_row.singpass_authenticated
      and state_row.insurance_completed
      and state_row.questionnaire_completed
    ) then
      raise exception 'onboarding_incomplete' using errcode = 'PT409';
    end if;
    state_row.completed := true;
    state_row.current_step := 'complete';
  end if;

  update public.patient_onboarding_states set
    current_step = state_row.current_step,
    completed = state_row.completed,
    singpass_authenticated = state_row.singpass_authenticated,
    insurance_completed = state_row.insurance_completed,
    questionnaire_completed = state_row.questionnaire_completed,
    singpass_profile = state_row.singpass_profile,
    version = version + 1
  where clerk_user_id = p_clerk_user_id
  returning * into state_row;

  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    'clinic_harbourfront',
    p_actor_reference, p_patient_id, 'advance_onboarding',
    'patient_onboarding_states', p_clerk_user_id,
    jsonb_build_object(
      'step', p_step,
      'current_step', state_row.current_step,
      'completed', state_row.completed
    )
  );

  existing_response := jsonb_build_object(
    'clerk_user_id', state_row.clerk_user_id,
    'patient_id', state_row.patient_id,
    'appointment_id', state_row.appointment_reference,
    'current_step', state_row.current_step,
    'completed', state_row.completed,
    'singpass_authenticated', state_row.singpass_authenticated,
    'insurance_completed', state_row.insurance_completed,
    'questionnaire_completed', state_row.questionnaire_completed,
    'singpass_profile', state_row.singpass_profile,
    'version', state_row.version
  );
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('onboarding_advance', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

alter table public.patient_onboarding_states
  alter column appointment_reference set default '';

revoke all on function public.epicenter_submit_onboarding_coverage(bigint, text, text, text, text)
  from public, anon, authenticated;
grant execute on function public.epicenter_submit_onboarding_coverage(bigint, text, text, text, text)
  to service_role;

comment on function public.epicenter_submit_onboarding_coverage(bigint, text, text, text, text) is
  'Stores first-time patient coverage without requiring an appointment booking.';

commit;
