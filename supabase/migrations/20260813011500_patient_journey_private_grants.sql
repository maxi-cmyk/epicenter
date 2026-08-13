-- Allow service_role patient journey RPCs to call private helpers.
begin;

grant usage on schema private to service_role;
grant execute on function private.epicenter_payment_payload(public.payments) to service_role;
grant execute on function private.epicenter_ensure_payment_for_appointment(bigint, public.appointments)
  to service_role;

commit;
