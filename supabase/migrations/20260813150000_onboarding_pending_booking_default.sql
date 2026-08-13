-- Stop seeding first-time onboarding to APT-DEMO-014 when the patient has no booking.
begin;

alter table public.patient_onboarding_states
  alter column appointment_reference set default 'pending-booking';

update public.patient_onboarding_states as state
set appointment_reference = 'pending-booking'
where nullif(trim(state.appointment_reference), '') is null
   or (
     state.appointment_reference not in ('pending-booking', 'PENDING')
     and not exists (
       select 1
       from public.appointments as appointment
       where appointment.appointment_reference = state.appointment_reference
         and appointment.patient_id = state.patient_id
         and appointment.deleted_at is null
     )
   );

create or replace function public.epicenter_get_onboarding(
  p_clerk_user_id text,
  p_patient_id bigint,
  p_appointment_reference text default 'pending-booking'
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  state_row public.patient_onboarding_states%rowtype;
  appointment_ref text;
  owned boolean;
begin
  if nullif(trim(p_clerk_user_id), '') is null or p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  appointment_ref := coalesce(nullif(trim(p_appointment_reference), ''), 'pending-booking');
  if appointment_ref in ('PENDING') then
    appointment_ref := 'pending-booking';
  end if;

  select * into state_row from public.patient_onboarding_states
  where clerk_user_id = p_clerk_user_id;
  if not found then
    insert into public.patient_onboarding_states (
      clerk_user_id, patient_id, appointment_reference
    ) values (
      p_clerk_user_id, p_patient_id, appointment_ref
    ) returning * into state_row;
  elsif state_row.patient_id <> p_patient_id then
    raise exception 'onboarding_patient_mismatch' using errcode = 'PT409';
  end if;

  appointment_ref := coalesce(nullif(trim(state_row.appointment_reference), ''), 'pending-booking');
  if appointment_ref not in ('pending-booking', 'PENDING') then
    select exists (
      select 1
      from public.appointments
      where appointment_reference = appointment_ref
        and patient_id = p_patient_id
        and deleted_at is null
    ) into owned;
    if not owned then
      appointment_ref := 'pending-booking';
      update public.patient_onboarding_states
      set appointment_reference = 'pending-booking'
      where clerk_user_id = p_clerk_user_id
      returning * into state_row;
    end if;
  else
    appointment_ref := 'pending-booking';
  end if;

  return jsonb_build_object(
    'clerk_user_id', state_row.clerk_user_id,
    'patient_id', state_row.patient_id,
    'appointment_id', appointment_ref,
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

commit;
