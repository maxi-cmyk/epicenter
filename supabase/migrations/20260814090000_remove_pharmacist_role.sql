-- The pharmacy screen and pharmacist role have been removed from the product.
-- Drop 'pharmacist' from the staff_accounts.role allowlist without rewriting
-- the already-applied 20260812020734_operational_persistence.sql migration.
begin;

alter table public.staff_accounts
  drop constraint staff_accounts_role_check;

alter table public.staff_accounts
  add constraint staff_accounts_role_check
  check (role in ('registration', 'billing', 'operations_admin', 'auditor'));

commit;
