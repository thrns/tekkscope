-- Apply this migration before enabling hashed API-key creation in production.
-- Existing plaintext keys remain valid through the compatibility lookup until
-- they are rotated by their owners.

alter table if exists public.api_keys
  add column if not exists api_key_hash text;

alter table if exists public.api_keys
  add column if not exists api_key_prefix text;

create index if not exists api_keys_user_id_idx
  on public.api_keys (user_id);

create index if not exists api_keys_prefix_idx
  on public.api_keys (api_key_prefix);

create unique index if not exists api_keys_hash_unique_idx
  on public.api_keys (api_key_hash)
  where api_key_hash is not null;

-- The backend uses the service role for these operations. This policy protects
-- browser-facing Supabase access if a client is granted table access later.
alter table if exists public.api_keys enable row level security;

drop policy if exists "Users can read their own api keys" on public.api_keys;
create policy "Users can read their own api keys"
  on public.api_keys for select
  using (auth.uid()::text = user_id::text);

drop policy if exists "Users can delete their own api keys" on public.api_keys;
create policy "Users can delete their own api keys"
  on public.api_keys for delete
  using (auth.uid()::text = user_id::text);
