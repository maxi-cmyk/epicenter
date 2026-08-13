-- Patients see the same queue number and counter assignment as the nurse board.

create or replace function private.epicenter_patient_assignment(p_queue public.queue_entries)
returns jsonb
language sql
stable
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'queue_number', coalesce(nullif(btrim(p_queue.queue_number), ''), p_queue.expected_queue_number, p_queue.id),
    'counter_label', coalesce(p_queue.counter_number, p_queue.expected_counter_number)
  );
$$;

create or replace function public.epicenter_get_patient_queue(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  queue_row public.queue_entries%rowtype;
  payment_row public.payments%rowtype;
  assignment jsonb;
  patients_ahead integer := 0;
  available boolean := false;
  checked_in boolean := false;
  status_label text := 'Before check-in';
  status_detail text := 'Your queue number and counter will appear once the clinic assigns them.';
  queue_number text := null;
  counter_label text := null;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select * into queue_row from public.queue_entries
  where patient_id = p_patient_id
    and deleted_at is null
    and visit_status in ('incoming', 'ongoing')
  order by
    case when visit_status = 'ongoing' then 0 else 1 end,
    coalesce(checked_in_at, original_ordering_at) desc
  limit 1;

  if not found then
    select * into queue_row from public.queue_entries
    where patient_id = p_patient_id and deleted_at is null
    order by coalesce(completed_at, updated_at) desc
    limit 1;
  end if;

  if not found then
    return jsonb_build_object(
      'synthetic', true,
      'available', false,
      'ticket_id', null,
      'visit_phase', null,
      'status_label', 'No active ticket',
      'status_detail', 'Your queue ticket will appear once the clinic opens your visit.',
      'queue_number', null,
      'counter_label', null,
      'patients_ahead', null,
      'updated_at', now(),
      'stale', false,
      'payment_ready', false
    );
  end if;

  assignment := private.epicenter_patient_assignment(queue_row);
  queue_number := assignment->>'queue_number';
  counter_label := assignment->>'counter_label';
  checked_in := queue_row.checked_in_at is not null or queue_row.visit_status <> 'incoming';
  available := queue_number is not null or counter_label is not null;

  if queue_row.readiness_state = 'needs_review' then
    status_label := 'Additional review needed';
    status_detail := coalesce(nullif(btrim(queue_row.patient_next_action), ''),
      'A staff member is reviewing your registration.');
  elsif queue_row.readiness_state = 'processing' then
    status_label := 'Processing';
    status_detail := 'We are checking your registration details.';
  elsif queue_row.visit_status = 'finished' then
    status_label := 'Finished';
    status_detail := 'Your visit is complete.';
  elsif not checked_in then
    status_label := 'Ticket reserved';
    status_detail := 'Your queue number and counter are ready. Keep this ticket for arrival.';
  else
    status_label := 'Waiting';
    status_detail := 'Waiting to be called. Keep this ticket — you will not take another number.';
  end if;

  if checked_in then
    select count(*) into patients_ahead
    from public.queue_entries other
    where other.clinic_id = queue_row.clinic_id
      and other.deleted_at is null
      and other.visit_status = 'ongoing'
      and other.id <> queue_row.id
      and coalesce(other.checked_in_at, other.original_ordering_at)
        < coalesce(queue_row.checked_in_at, queue_row.original_ordering_at);
  end if;

  if queue_row.appointment_id is not null then
    select * into payment_row from public.payments
    where appointment_id = queue_row.appointment_id;
  end if;

  return jsonb_build_object(
    'synthetic', true,
    'available', available,
    'ticket_id', queue_row.id,
    'visit_phase', queue_row.visit_status,
    'status_label', status_label,
    'status_detail', status_detail,
    'queue_number', queue_number,
    'counter_label', counter_label,
    'patients_ahead', case when checked_in then patients_ahead else null end,
    'updated_at', queue_row.updated_at,
    'stale', false,
    'payment_ready', coalesce(payment_row.status, 'not_ready')
      in ('ready', 'mocked_paid', 'mock_failed')
  );
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
  assignment jsonb;
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
      assignment := private.epicenter_patient_assignment(queue_row);
      if assignment->>'counter_label' is not null then
        queue_summary := format('%s · Counter %s', assignment->>'queue_number', assignment->>'counter_label');
      else
        queue_summary := format('Ticket %s', assignment->>'queue_number');
      end if;
    else
      queue_summary := 'Queue number assigned at the clinic';
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

grant execute on function private.epicenter_patient_assignment(public.queue_entries) to service_role;
