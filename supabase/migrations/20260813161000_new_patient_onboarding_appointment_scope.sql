-- Prevent newly created patients from inheriting the seeded demo appointment.
begin;

update public.patient_onboarding_states state
set appointment_reference = '',
    version = version + 1,
    updated_at = now()
where nullif(trim(state.appointment_reference), '') is not null
  and state.appointment_reference not in ('pending-booking', 'PENDING')
  and not exists (
    select 1
    from public.appointments appointment
    where appointment.appointment_reference = state.appointment_reference
      and appointment.patient_id = state.patient_id
      and appointment.deleted_at is null
  );

create or replace function public.epicenter_get_onboarding(
  p_clerk_user_id text,
  p_patient_id bigint,
  p_appointment_reference text default ''
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  state_row public.patient_onboarding_states%rowtype;
  requested_appointment text;
begin
  if nullif(trim(p_clerk_user_id), '') is null or p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  requested_appointment := coalesce(nullif(trim(p_appointment_reference), ''), '');
  if requested_appointment <> '' and not exists (
    select 1
    from public.appointments appointment
    where appointment.appointment_reference = requested_appointment
      and appointment.patient_id = p_patient_id
      and appointment.deleted_at is null
  ) then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;

  insert into public.patient_onboarding_states (
    clerk_user_id, patient_id, appointment_reference
  ) values (
    p_clerk_user_id, p_patient_id, requested_appointment
  )
  on conflict (clerk_user_id) do nothing;

  select * into state_row
  from public.patient_onboarding_states
  where clerk_user_id = p_clerk_user_id;

  if state_row.patient_id <> p_patient_id then
    raise exception 'onboarding_patient_mismatch' using errcode = 'PT409';
  end if;

  if nullif(trim(state_row.appointment_reference), '') is not null
     and state_row.appointment_reference not in ('pending-booking', 'PENDING')
     and not exists (
       select 1
       from public.appointments appointment
       where appointment.appointment_reference = state_row.appointment_reference
         and appointment.patient_id = p_patient_id
         and appointment.deleted_at is null
     ) then
    update public.patient_onboarding_states
    set appointment_reference = '', version = version + 1, updated_at = now()
    where clerk_user_id = p_clerk_user_id
    returning * into state_row;
  end if;

  return jsonb_build_object(
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
end;
$$;

revoke all on function public.epicenter_get_onboarding(text, bigint, text)
  from public, anon, authenticated;
grant execute on function public.epicenter_get_onboarding(text, bigint, text)
  to service_role;

comment on function public.epicenter_get_onboarding(text, bigint, text)
  is 'Returns or initializes onboarding without assigning an appointment not owned by the patient.';

notify pgrst, 'reload schema';
commit;
