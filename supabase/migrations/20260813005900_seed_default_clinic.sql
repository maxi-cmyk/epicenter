-- The demo clinic row is referenced by later migrations (patient journey
-- persistence, onboarding coverage RPCs, real-patient empty states) as well
-- as by supabase/operational_seed.sql. Seed files only run after all
-- migrations have applied, so any migration-time insert that references
-- 'clinic_harbourfront' needs the row to already exist. This migration
-- creates it before the first such reference
-- (20260813010000_patient_journey_persistence.sql).
begin;

insert into public.clinics (id, name)
values ('clinic_harbourfront', 'Parkway Shenton · HarbourFront')
on conflict (id) do update set
  name = excluded.name;

commit;
