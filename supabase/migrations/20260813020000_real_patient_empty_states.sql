-- Real patient accounts: questionnaire without a booking; empty payment when unbooked.
begin;

alter table public.appointment_questionnaire_responses
  alter column appointment_id drop not null;

alter table public.appointment_questionnaire_responses
  drop constraint if exists appointment_questionnaire_responses_appointment_id_patient_id_key;

create unique index if not exists appointment_questionnaire_responses_appointment_patient_uidx
  on public.appointment_questionnaire_responses (appointment_id, patient_id)
  where appointment_id is not null;

create unique index if not exists appointment_questionnaire_responses_patient_pending_uidx
  on public.appointment_questionnaire_responses (patient_id)
  where appointment_id is null;

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
  appointment_ref text;
begin
  if p_patient_id is null then
    raise exception 'questionnaire_identity_required' using errcode = 'PT422';
  end if;

  appointment_ref := nullif(trim(coalesce(p_appointment_reference, '')), '');
  if appointment_ref is null or appointment_ref in ('pending-booking', 'PENDING') then
    select * into response_row from public.appointment_questionnaire_responses
    where patient_id = p_patient_id and appointment_id is null;
    if not found then
      insert into public.appointment_questionnaire_responses (appointment_id, patient_id)
      values (null, p_patient_id)
      returning * into response_row;
    end if;
    return jsonb_build_object(
      'appointment_id', 'pending-booking',
      'appointment_db_id', null,
      'patient_id', response_row.patient_id,
      'answers', response_row.answers,
      'declaration_acknowledged', response_row.declaration_acknowledged,
      'status', response_row.status,
      'version', response_row.version
    );
  end if;

  select * into appointment_row from public.appointments
  where appointment_reference = appointment_ref
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
  appointment_ref text;
  result_appointment_id text;
begin
  perform pg_advisory_xact_lock(hashtextextended('questionnaire_save:' || p_idempotency_key, 0));
  select response_payload into existing_response from public.idempotency_records
  where operation = 'questionnaire_save' and idempotency_key = p_idempotency_key;
  if existing_response is not null then return existing_response; end if;

  if p_patient_id is null then
    raise exception 'questionnaire_identity_required' using errcode = 'PT422';
  end if;

  appointment_ref := nullif(trim(coalesce(p_appointment_reference, '')), '');
  next_status := case when p_submit then 'submitted' else 'draft' end;

  if appointment_ref is null or appointment_ref in ('pending-booking', 'PENDING') then
    select * into response_row from public.appointment_questionnaire_responses
    where patient_id = p_patient_id and appointment_id is null
    for update;
    if not found then
      insert into public.appointment_questionnaire_responses (appointment_id, patient_id)
      values (null, p_patient_id)
      returning * into response_row;
      select * into response_row from public.appointment_questionnaire_responses
      where id = response_row.id for update;
    end if;
    if response_row.version <> p_expected_version then
      raise exception 'questionnaire_version_conflict' using errcode = 'PT409';
    end if;
    update public.appointment_questionnaire_responses set
      answers = coalesce(p_answers, '{}'::jsonb),
      declaration_acknowledged = coalesce(p_declaration_acknowledged, false),
      status = next_status,
      version = version + 1
    where id = response_row.id
    returning * into response_row;
    result_appointment_id := 'pending-booking';
  else
    select * into appointment_row from public.appointments
    where appointment_reference = appointment_ref
      and patient_id = p_patient_id
      and deleted_at is null;
    if not found then
      raise exception 'appointment_not_found' using errcode = 'PT404';
    end if;
    select * into response_row from public.appointment_questionnaire_responses
    where appointment_id = appointment_row.id and patient_id = p_patient_id
    for update;
    if not found then
      insert into public.appointment_questionnaire_responses (appointment_id, patient_id)
      values (appointment_row.id, p_patient_id)
      returning * into response_row;
      select * into response_row from public.appointment_questionnaire_responses
      where id = response_row.id for update;
    end if;
    if response_row.version <> p_expected_version then
      raise exception 'questionnaire_version_conflict' using errcode = 'PT409';
    end if;
    update public.appointment_questionnaire_responses set
      answers = coalesce(p_answers, '{}'::jsonb),
      declaration_acknowledged = coalesce(p_declaration_acknowledged, false),
      status = next_status,
      version = version + 1
    where id = response_row.id
    returning * into response_row;
    result_appointment_id := appointment_row.appointment_reference;
  end if;

  existing_response := jsonb_build_object(
    'appointment_id', result_appointment_id,
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

create or replace function public.epicenter_get_patient_payment(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  appointment_row public.appointments%rowtype;
  payment_row public.payments%rowtype;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into appointment_row from public.appointments
  where patient_id = p_patient_id
    and deleted_at is null
    and status in ('booked', 'checked_in', 'completed')
  order by
    case when status in ('booked', 'checked_in') then 0 else 1 end,
    scheduled_at desc
  limit 1;
  if not found then
    return jsonb_build_object(
      'synthetic', false,
      'mocked', true,
      'appointment_id', null,
      'package_label', 'No appointment has been made',
      'amount_covered', '—',
      'amount_patient_payable', '—',
      'status', 'not_ready',
      'status_detail', 'Payment appears after the clinic books your visit and finalises billing.',
      'receipt_reference', null,
      'paid_at', null,
      'failure_reason', null,
      'version', 1
    );
  end if;

  payment_row := private.epicenter_ensure_payment_for_appointment(p_patient_id, appointment_row);
  return private.epicenter_payment_payload(payment_row);
end;
$$;

create or replace function public.epicenter_get_patient_home(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  patient_row public.patients%rowtype;
  appointment_row public.appointments%rowtype;
  clinic_row public.clinics%rowtype;
  queue_row public.queue_entries%rowtype;
  payment_row public.payments%rowtype;
  onboarding_row public.patient_onboarding_states%rowtype;
  questionnaire_row public.appointment_questionnaire_responses%rowtype;
  notification_row public.patient_notifications%rowtype;
  coverage_count integer := 0;
  coverage_status text := 'not_started';
  coverage_summary text := 'Coverage document still needed';
  questionnaire_status text := 'not_started';
  questionnaire_summary text := 'General health questionnaire not started';
  payment_status text := 'not_ready';
  payment_summary text := 'No appointment has been made';
  primary_action text := 'none';
  primary_label text := 'No appointment has been made';
  primary_href text := '/';
  queue_summary text := 'No appointment has been made';
  outcome_value text := null;
  outcome_message text := null;
  recent_visit text := null;
  notification_payload jsonb := null;
  appointment_payload jsonb := null;
  display_name text;
  profile_name text;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into patient_row from public.patients
  where id = p_patient_id and deleted_at is null;
  if not found then
    raise exception 'patient_not_found' using errcode = 'PT404';
  end if;

  select * into onboarding_row from public.patient_onboarding_states
  where patient_id = p_patient_id
  order by updated_at desc
  limit 1;

  display_name := patient_row.full_name;
  if onboarding_row.singpass_profile is not null then
    select elem->>'value' into profile_name
    from jsonb_array_elements(onboarding_row.singpass_profile) elem
    where elem->>'field_id' = 'full_name'
    limit 1;
    if nullif(trim(coalesce(profile_name, '')), '') is not null then
      display_name := trim(profile_name);
    end if;
  end if;

  select * into appointment_row from public.appointments
  where patient_id = p_patient_id
    and deleted_at is null
    and status in ('booked', 'checked_in')
  order by scheduled_at asc
  limit 1;

  if found then
    select * into clinic_row from public.clinics where id = appointment_row.clinic_id;
    appointment_payload := jsonb_build_object(
      'appointment_id', appointment_row.appointment_reference,
      'scheduled_at', appointment_row.scheduled_at,
      'clinic_name', coalesce(clinic_row.name, appointment_row.clinic_id),
      'location', coalesce(clinic_row.name, 'Clinic'),
      'appointment_type', appointment_row.appointment_type,
      'questionnaire_type', coalesce(appointment_row.questionnaire_type, 'general_health')
    );

    select * into queue_row from public.queue_entries
    where appointment_id = appointment_row.id and deleted_at is null
    limit 1;
    if found then
      outcome_value := queue_row.patient_outcome;
      outcome_message := queue_row.patient_next_action;
      if queue_row.checked_in_at is not null or queue_row.visit_status <> 'incoming' then
        queue_summary := format('Ticket %s · %s', queue_row.id, initcap(queue_row.visit_status));
      else
        queue_summary := format('Ticket %s reserved — status after check-in', queue_row.id);
      end if;
    else
      queue_summary := 'Available after staff check-in';
    end if;

    payment_row := private.epicenter_ensure_payment_for_appointment(p_patient_id, appointment_row);
    payment_status := payment_row.status;
    payment_summary := case payment_row.status
      when 'not_ready' then 'Not ready — staff still finalising billing'
      when 'ready' then 'Demo payment ready'
      when 'mock_processing' then 'Demo payment processing'
      when 'mocked_paid' then 'Demo payment recorded'
      when 'mock_failed' then 'Demo payment failed — retry available'
      else 'Payment status unavailable'
    end;

    select * into questionnaire_row from public.appointment_questionnaire_responses
    where appointment_id = appointment_row.id
      and patient_id = p_patient_id
    limit 1;
    if found then
      questionnaire_status := questionnaire_row.status;
    elsif appointment_row.questionnaire_type is null then
      questionnaire_status := 'not_required';
    end if;
  end if;

  select count(*) into coverage_count from public.coverage_documents
  where patient_id = p_patient_id and deleted_at is null;

  select * into notification_row from public.patient_notifications
  where patient_id = p_patient_id
    and patient_action = 'none'
  order by sent_at desc
  limit 1;
  if found then
    coverage_status := 'action_required';
    coverage_summary := case notification_row.category
      when 'document_unclear' then 'Please upload a clearer coverage document'
      when 'document_incomplete' then 'Your coverage document is incomplete'
      when 'document_expired' then 'Your coverage document has expired'
      else 'Please upload a current coverage document'
    end;
    notification_payload := jsonb_build_object(
      'category', notification_row.category,
      'message', coverage_summary,
      'next_action', 'Upload a replacement coverage document'
    );
  elsif coverage_count > 0 or coalesce(onboarding_row.insurance_completed, false) then
    coverage_status := 'submitted';
    coverage_summary := 'Coverage received for staff confirmation';
  else
    coverage_status := 'not_started';
    coverage_summary := 'Coverage document still needed';
  end if;

  if appointment_payload is null then
    select * into questionnaire_row from public.appointment_questionnaire_responses
    where patient_id = p_patient_id and appointment_id is null
    limit 1;
    if found then
      questionnaire_status := questionnaire_row.status;
    elsif coalesce(onboarding_row.questionnaire_completed, false) then
      questionnaire_status := 'submitted';
    end if;
  end if;

  if questionnaire_status = 'not_required' then
    questionnaire_summary := 'No questionnaire required';
  elsif coalesce(onboarding_row.questionnaire_completed, false)
     or questionnaire_status = 'submitted' then
    questionnaire_status := 'submitted';
    questionnaire_summary := 'Questionnaire submitted';
  elsif questionnaire_status = 'draft' then
    questionnaire_summary := 'Questionnaire draft saved — finish and submit';
  else
    questionnaire_status := 'not_started';
    questionnaire_summary := 'General health questionnaire not started';
  end if;

  if appointment_payload is null then
    primary_action := 'none';
    primary_label := 'No appointment has been made';
    primary_href := '/';
    queue_summary := 'No appointment has been made';
    payment_summary := 'No appointment has been made';
  elsif coverage_status in ('not_started', 'check_first', 'action_required') then
    primary_action := 'confirm_coverage';
    primary_label := 'Confirm coverage for this visit';
    primary_href := '/coverage';
  elsif questionnaire_status not in ('submitted', 'not_required') then
    primary_action := 'complete_questionnaire';
    primary_label := 'Complete the required questionnaire';
    primary_href := '/questionnaire';
  elsif payment_status in ('ready', 'mock_failed') then
    primary_action := 'pay';
    primary_label := case when payment_status = 'mock_failed'
      then 'Retry demo payment' else 'Complete demo payment' end;
    primary_href := '/payment';
  elsif outcome_value = 'under_review' then
    primary_action := 'wait_for_review';
    primary_label := 'See your current status';
    primary_href := '/queue';
  else
    primary_action := 'view_queue';
    primary_label := 'View queue status';
    primary_href := '/queue';
  end if;

  select format(
    '%s · %s',
    to_char(a.scheduled_at at time zone 'Asia/Singapore', 'DD Mon YYYY'),
    replace(initcap(replace(a.appointment_type, '_', ' ')), 'Gp', 'GP')
  )
  into recent_visit
  from public.appointments a
  where a.patient_id = p_patient_id
    and a.deleted_at is null
    and a.status = 'completed'
  order by a.scheduled_at desc
  limit 1;

  return jsonb_build_object(
    'synthetic', coalesce(patient_row.is_synthetic, false),
    'patient_display_name', display_name,
    'appointment', appointment_payload,
    'coverage_status', coverage_status,
    'coverage_summary', coverage_summary,
    'questionnaire_status', questionnaire_status,
    'queue_summary', queue_summary,
    'payment_status', payment_status,
    'payment_summary', payment_summary,
    'primary_action', primary_action,
    'primary_action_label', primary_label,
    'primary_action_href', primary_href,
    'outcome', outcome_value,
    'outcome_message', outcome_message,
    'notification', notification_payload,
    'recent_visit_summary', recent_visit
  );
end;
$$;

-- Onboarding advance: questionnaire may be patient-pending (no appointment yet).
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
      and deleted_at is null
      and appointment_id is null;
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
    questionnaire_row := null;
    if nullif(trim(state_row.appointment_reference), '') is not null
       and state_row.appointment_reference not in ('pending-booking', 'PENDING') then
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
      select * into questionnaire_row from public.appointment_questionnaire_responses
      where patient_id = p_patient_id and appointment_id is null;
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
    'appointment_id', coalesce(nullif(trim(state_row.appointment_reference), ''), 'pending-booking'),
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

commit;
