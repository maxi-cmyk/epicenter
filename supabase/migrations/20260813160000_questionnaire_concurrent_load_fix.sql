-- Make questionnaire initialization safe when multiple client loads arrive together.
begin;

create or replace function public.epicenter_get_questionnaire(
  p_appointment_reference text,
  p_patient_id bigint
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
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
    insert into public.appointment_questionnaire_responses (appointment_id, patient_id)
    values (null, p_patient_id)
    on conflict (patient_id) where appointment_id is null do nothing;

    select * into response_row
    from public.appointment_questionnaire_responses
    where patient_id = p_patient_id and appointment_id is null;

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

  select * into appointment_row
  from public.appointments
  where appointment_reference = appointment_ref
    and patient_id = p_patient_id
    and deleted_at is null;
  if not found then
    raise exception 'appointment_not_found' using errcode = 'PT404';
  end if;

  insert into public.appointment_questionnaire_responses (appointment_id, patient_id)
  values (appointment_row.id, p_patient_id)
  on conflict (appointment_id, patient_id) where appointment_id is not null do nothing;

  select * into response_row
  from public.appointment_questionnaire_responses
  where appointment_id = appointment_row.id and patient_id = p_patient_id;

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

revoke all on function public.epicenter_get_questionnaire(text, bigint)
  from public, anon, authenticated;
grant execute on function public.epicenter_get_questionnaire(text, bigint)
  to service_role;

comment on function public.epicenter_get_questionnaire(text, bigint)
  is 'Returns or atomically initializes one patient questionnaire without concurrent first-load conflicts.';

notify pgrst, 'reload schema';
commit;
