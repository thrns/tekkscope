-- Optional additive metadata for usage and billing observability.
-- The application falls back to the legacy usage payload until this is applied.

alter table if exists public.usage
  add column if not exists provider text;

alter table if exists public.usage
  add column if not exists model text;

alter table if exists public.usage
  add column if not exists token_count_estimated boolean not null default true;

create index if not exists usage_api_token_timestamp_idx
  on public.usage (api_token_id, timestamp);

create index if not exists usage_user_timestamp_idx
  on public.usage (user_id, timestamp);
