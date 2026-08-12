begin;

create table public.patient_onboarding_states (
  clerk_user_id text primary key,
  patient_id bigint not null references public.patients(id) on delete restrict,
  appointment_reference text not null default 'APT-DEMO-014',
  current_step text not null default 'singpass'
    check (current_step in ('singpass', 'insurance', 'questionnaire', 'complete')),
  completed boolean not null default false,
  singpass_authenticated boolean not null default false,
  insurance_completed boolean not null default false,
  questionnaire_completed boolean not null default false,
  singpass_profile jsonb not null default '[]'::jsonb,
  version integer not null default 1 check (version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index patient_onboarding_states_patient_id_idx
  on public.patient_onboarding_states (patient_id);

create table public.appointment_questionnaire_responses (
  id bigint generated always as identity primary key,
  appointment_id text not null references public.appointments(id) on delete restrict,
  patient_id bigint not null references public.patients(id) on delete restrict,
  answers jsonb not null default '{}'::jsonb,
  declaration_acknowledged boolean not null default false,
  status text not null default 'draft'
    check (status in ('draft', 'submitted')),
  version integer not null default 1 check (version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (appointment_id, patient_id)
);
create index appointment_questionnaire_responses_patient_idx
  on public.appointment_questionnaire_responses (patient_id, updated_at desc);

create trigger patient_onboarding_states_set_updated_at
  before update on public.patient_onboarding_states
  for each row execute function private.set_updated_at();
create trigger appointment_questionnaire_responses_set_updated_at
  before update on public.appointment_questionnaire_responses
  for each row execute function private.set_updated_at();

create or replace function public.epicenter_get_onboarding(
  p_clerk_user_id text,
  p_patient_id bigint,
  p_appointment_reference text default 'APT-DEMO-014'
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  state_row public.patient_onboarding_states%rowtype;
begin
  if nullif(trim(p_clerk_user_id), '') is null or p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into state_row from public.patient_onboarding_states
  where clerk_user_id = p_clerk_user_id;
  if not found then
    insert into public.patient_onboarding_states (
      clerk_user_id, patient_id, appointment_reference
    ) values (
      p_clerk_user_id, p_patient_id, coalesce(nullif(trim(p_appointment_reference), ''), 'APT-DEMO-014')
    ) returning * into state_row;
  elsif state_row.patient_id <> p_patient_id then
    raise exception 'onboarding_patient_mismatch' using errcode = 'PT409';
  end if;

  return jsonb_build_object(
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
end;
$$;

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
  submission_count integer;
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
      coalesce(nullif(trim(p_appointment_reference), ''), 'APT-DEMO-014')
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
    select * into appointment_row from public.appointments
    where appointment_reference = state_row.appointment_reference
      and patient_id = p_patient_id
      and deleted_at is null;
    if not found then
      raise exception 'appointment_not_found' using errcode = 'PT404';
    end if;
    select count(*) into submission_count from public.patient_submissions
    where appointment_id = appointment_row.id
      and patient_id = p_patient_id
      and deleted_at is null
      and actor_reference = p_clerk_user_id;
    if submission_count < 1 then
      raise exception 'coverage_submission_required' using errcode = 'PT409';
    end if;
    if was_insurance_completed or coalesce(p_insurance_completed, false) then
      state_row.current_step := 'questionnaire';
    end if;
  elsif p_step = 'questionnaire' then
    if not state_row.questionnaire_completed then
      raise exception 'questionnaire_required' using errcode = 'PT409';
    end if;
    select * into appointment_row from public.appointments
    where appointment_reference = state_row.appointment_reference
      and patient_id = p_patient_id
      and deleted_at is null;
    if not found then
      raise exception 'appointment_not_found' using errcode = 'PT404';
    end if;
    select * into questionnaire_row from public.appointment_questionnaire_responses
    where appointment_id = appointment_row.id and patient_id = p_patient_id;
    if not found or questionnaire_row.status <> 'submitted' then
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
  )
  select
    a.clinic_id, p_actor_reference, p_patient_id, 'advance_onboarding',
    'patient_onboarding_states', p_clerk_user_id,
    jsonb_build_object(
      'step', p_step,
      'current_step', state_row.current_step,
      'completed', state_row.completed
    )
  from public.appointments a
  where a.appointment_reference = state_row.appointment_reference
    and a.deleted_at is null
  limit 1;

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

create or replace function public.epicenter_get_questionnaire(
  p_appointment_reference text,
  p_patient_id bigint
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  appointment_row public.appointments%rowtype;
  response_row public.appointment_questionnaire_responses%rowtype;
begin
  if nullif(trim(p_appointment_reference), '') is null or p_patient_id is null then
    raise exception 'questionnaire_identity_required' using errcode = 'PT422';
  end if;

  select * into appointment_row from public.appointments
  where appointment_reference = p_appointment_reference
    and patient_id = p_patient_id
    and deleted_at is null;
  if not found then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;

  select * into response_row from public.appointment_questionnaire_responses
  where appointment_id = appointment_row.id and patient_id = p_patient_id;
  if not found then
    insert into public.appointment_questionnaire_responses (
      appointment_id, patient_id
    ) values (
      appointment_row.id, p_patient_id
    ) returning * into response_row;
  end if;

  return jsonb_build_object(
    'appointment_id', appointment_row.appointment_reference,
    'appointment_db_id', appointment_row.id,
    'patient_id', response_row.patient_id,
    'answers', response_row.answers,
    'declaration_acknowledged', response_row.declaration_acknowledged,
    'status', response_row.status,
    'version', response_row.version
  );
end;
$$;

create or replace function public.epicenter_save_questionnaire(
  p_appointment_reference text,
  p_patient_id bigint,
  p_answers jsonb,
  p_declaration_acknowledged boolean,
  p_submit boolean,
  p_expected_version integer,
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
  appointment_row public.appointments%rowtype;
  response_row public.appointment_questionnaire_responses%rowtype;
  next_status text;
begin
  perform pg_advisory_xact_lock(hashtextextended('questionnaire_save:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'questionnaire_save' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;

  if nullif(trim(p_appointment_reference), '') is null or p_patient_id is null then
    raise exception 'questionnaire_identity_required' using errcode = 'PT422';
  end if;

  select * into appointment_row from public.appointments
  where appointment_reference = p_appointment_reference
    and patient_id = p_patient_id
    and deleted_at is null
  for update;
  if not found then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;

  select * into response_row from public.appointment_questionnaire_responses
  where appointment_id = appointment_row.id and patient_id = p_patient_id
  for update;
  if not found then
    insert into public.appointment_questionnaire_responses (
      appointment_id, patient_id
    ) values (
      appointment_row.id, p_patient_id
    ) returning * into response_row;
    select * into response_row from public.appointment_questionnaire_responses
    where appointment_id = appointment_row.id and patient_id = p_patient_id
    for update;
  end if;

  if response_row.version <> p_expected_version then
    raise exception 'stale_questionnaire_version' using errcode = 'PT409';
  end if;
  if response_row.status = 'submitted' then
    raise exception 'questionnaire_already_submitted' using errcode = 'PT409';
  end if;

  next_status := case when coalesce(p_submit, false) then 'submitted' else 'draft' end;

  update public.appointment_questionnaire_responses set
    answers = coalesce(p_answers, '{}'::jsonb),
    declaration_acknowledged = coalesce(p_declaration_acknowledged, false),
    status = next_status,
    version = version + 1
  where id = response_row.id
  returning * into response_row;

  insert into public.audit_log (
    clinic_id, actor_reference, patient_id, action_type, target_table, target_id, details
  ) values (
    appointment_row.clinic_id, p_actor_reference, p_patient_id, 'save_questionnaire',
    'appointment_questionnaire_responses', response_row.id::text,
    jsonb_build_object('status', response_row.status, 'appointment_reference', p_appointment_reference)
  );

  existing_response := jsonb_build_object(
    'appointment_id', appointment_row.appointment_reference,
    'appointment_db_id', appointment_row.id,
    'patient_id', response_row.patient_id,
    'answers', response_row.answers,
    'declaration_acknowledged', response_row.declaration_acknowledged,
    'status', response_row.status,
    'version', response_row.version
  );
  insert into public.idempotency_records (operation, idempotency_key, actor_reference, response_payload)
  values ('questionnaire_save', p_idempotency_key, p_actor_reference, existing_response);
  return existing_response;
end;
$$;

alter table public.patient_onboarding_states enable row level security;
alter table public.appointment_questionnaire_responses enable row level security;

revoke all on table public.patient_onboarding_states from anon, authenticated;
revoke all on table public.appointment_questionnaire_responses from anon, authenticated;
revoke all on sequence public.appointment_questionnaire_responses_id_seq from anon, authenticated;

revoke all on function public.epicenter_get_onboarding(text, bigint, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_advance_onboarding(text, bigint, text, boolean, boolean, boolean, jsonb, text, text, text)
  from public, anon, authenticated;
revoke all on function public.epicenter_get_questionnaire(text, bigint)
  from public, anon, authenticated;
revoke all on function public.epicenter_save_questionnaire(text, bigint, jsonb, boolean, boolean, integer, text, text)
  from public, anon, authenticated;

grant select, insert, update, delete on table public.patient_onboarding_states to service_role;
grant select, insert, update, delete on table public.appointment_questionnaire_responses to service_role;
grant usage, select on sequence public.appointment_questionnaire_responses_id_seq to service_role;
grant execute on function public.epicenter_get_onboarding(text, bigint, text) to service_role;
grant execute on function public.epicenter_advance_onboarding(text, bigint, text, boolean, boolean, boolean, jsonb, text, text, text)
  to service_role;
grant execute on function public.epicenter_get_questionnaire(text, bigint) to service_role;
grant execute on function public.epicenter_save_questionnaire(text, bigint, jsonb, boolean, boolean, integer, text, text)
  to service_role;

comment on table public.patient_onboarding_states is
  'First-time patient signup wizard progress keyed by Clerk subject.';
comment on table public.appointment_questionnaire_responses is
  'Runtime appointment-scoped questionnaire answers for signed-in patients.';

commit;
