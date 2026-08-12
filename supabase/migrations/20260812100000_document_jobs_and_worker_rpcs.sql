-- Migration: document_jobs table + worker RPC functions
-- Adds asynchronous document processing infrastructure required by the
-- Python background worker (backend/worker.py).

-- ============================================================
-- document_jobs table
-- ============================================================

create type document_job_status as enum (
    'queued',
    'processing',
    'ready',
    'failed_retryable',
    'failed_final'
);

create table document_jobs (
    id                  uuid primary key default gen_random_uuid(),
    document_id         text        not null,
    storage_path        text        not null,
    status              document_job_status not null default 'queued',
    worker_id           text,
    retry_count         int         not null default 0,
    model_used          text,
    prompt_version      text,
    extraction_result   jsonb,
    overall_confidence  text,
    raw_response_id     text,
    failure_reason      text,
    created_at          timestamptz not null default now(),
    claimed_at          timestamptz,
    completed_at        timestamptz,
    failed_at           timestamptz,
    -- soft audit fields
    created_by          text,
    idempotency_key     text unique
);

-- Index for worker polling (queued jobs ordered by creation)
create index document_jobs_queued_idx
    on document_jobs (created_at)
    where status = 'queued';

-- Index for status lookups from the API
create index document_jobs_document_id_idx
    on document_jobs (document_id);

-- Append-only protection: prevent deletion or status regression
create or replace function protect_document_jobs()
returns trigger language plpgsql as $$
begin
    -- Never allow hard deletes
    if tg_op = 'DELETE' then
        raise exception 'document_jobs rows are immutable — use failed_final status instead.';
    end if;
    -- Never allow status to go backward (e.g. ready → queued)
    if tg_op = 'UPDATE' then
        if old.status = 'ready' and new.status != 'ready' then
            raise exception 'A ready document job cannot be moved to a different status.';
        end if;
        if old.status = 'failed_final' and new.status != 'failed_final' then
            raise exception 'A final-failed document job cannot be changed.';
        end if;
    end if;
    return new;
end;
$$;

create trigger document_jobs_immutability
    before update or delete on document_jobs
    for each row execute function protect_document_jobs();

-- RLS: service role has full access; browser/anon roles are denied entirely.
alter table document_jobs enable row level security;

create policy document_jobs_service_only
    on document_jobs
    for all
    to service_role
    using (true)
    with check (true);

-- ============================================================
-- RPC: claim_document_job
-- Atomically claims one queued job for a worker process.
-- Returns the claimed row, or an empty set if none available.
-- ============================================================

create or replace function claim_document_job(worker_id text)
returns setof document_jobs
language plpgsql
security definer
as $$
declare
    claimed document_jobs;
begin
    -- Lock and claim exactly one queued job
    select *
      into claimed
      from document_jobs
     where status = 'queued'
       and retry_count < 3
     order by created_at asc
     limit 1
     for update skip locked;

    if claimed.id is null then
        return;
    end if;

    update document_jobs
       set status     = 'processing',
           worker_id  = claim_document_job.worker_id,
           claimed_at = now()
     where id = claimed.id;

    return query
        select * from document_jobs where id = claimed.id;
end;
$$;

-- Retry-eligible failed jobs are re-queued by this separate function,
-- called by the worker after the stability window.
create or replace function requeue_retryable_jobs()
returns int
language plpgsql
security definer
as $$
declare
    n int;
begin
    with requeued as (
        update document_jobs
           set status    = 'queued',
               worker_id = null,
               claimed_at = null
         where status = 'failed_retryable'
           and retry_count < 3
           and failed_at < now() - interval '30 seconds'
        returning id
    )
    select count(*) into n from requeued;
    return n;
end;
$$;

-- ============================================================
-- RPC: create_signed_document_url
-- Returns a short-lived signed URL for a private storage object.
-- The worker calls this instead of storing long-lived URLs anywhere.
-- Note: this wraps storage.create_signed_url which is only available
-- when called with the service-role key — the worker always uses
-- EPICENTER_SUPABASE_SECRET_KEY.
-- ============================================================

create or replace function create_signed_document_url(
    storage_path text,
    expires_in   int default 120
)
returns json
language plpgsql
security definer
as $$
declare
    signed_url text;
    bucket_name text := 'documents';
begin
    -- Delegate to Supabase storage signed URL creation
    -- This requires the storage extension to be enabled and the bucket to exist.
    select storage.create_signed_url(bucket_name, storage_path, expires_in)
      into signed_url;

    return json_build_object('signed_url', signed_url);
exception
    when others then
        raise exception 'Failed to create signed URL for %: %', storage_path, sqlerrm;
end;
$$;
