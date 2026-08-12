-- Fix records aggregation alias for jsonb_agg ordering.
begin;

create or replace function public.epicenter_get_patient_records(p_patient_id bigint)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  visits jsonb := '[]'::jsonb;
begin
  if p_patient_id is null then
    raise exception 'patient_identity_required' using errcode = 'PT422';
  end if;

  select coalesce(jsonb_agg(ranked.visit_row order by ranked.sort_at desc), '[]'::jsonb)
  into visits
  from (
    select jsonb_build_object(
      'appointment_id', a.appointment_reference,
      'visited_on', (a.scheduled_at at time zone 'Asia/Singapore')::date,
      'visit_label', replace(initcap(replace(a.appointment_type, '_', ' ')), 'Gp', 'GP'),
      'package_label', pay.package_label,
      'coverage_label', cov.issuer_name,
      'questionnaire_summary', case
        when q.status = 'submitted' then 'General health · Submitted'
        when q.status = 'draft' then 'General health · Draft'
        when a.questionnaire_type is null then null
        else 'General health · Pending'
      end,
      'outcome', coalesce(qe.patient_outcome, sub.outcome)
    ) as visit_row,
    a.scheduled_at as sort_at
    from public.appointments a
    left join lateral (
      select p.package_label from public.payments p
      where p.appointment_id = a.id
      limit 1
    ) pay on true
    left join lateral (
      select cd.issuer_name from public.coverage_documents cd
      where cd.patient_id = a.patient_id
        and cd.deleted_at is null
        and (cd.appointment_id = a.id or cd.appointment_id is null)
      order by cd.created_at desc
      limit 1
    ) cov on true
    left join lateral (
      select aq.status from public.appointment_questionnaire_responses aq
      where aq.appointment_id = a.id
        and aq.patient_id = a.patient_id
      limit 1
    ) q on true
    left join lateral (
      select qe.patient_outcome from public.queue_entries qe
      where qe.appointment_id = a.id and qe.deleted_at is null
      limit 1
    ) qe on true
    left join lateral (
      select ps.outcome from public.patient_submissions ps
      where ps.appointment_id = a.id
        and ps.patient_id = a.patient_id
        and ps.deleted_at is null
      order by ps.created_at desc
      limit 1
    ) sub on true
    where a.patient_id = p_patient_id
      and a.deleted_at is null
  ) ranked;

  return jsonb_build_object(
    'synthetic', true,
    'visits', visits
  );
end;
$$;

commit;
