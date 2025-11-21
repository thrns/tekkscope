import { createClient, SupabaseClient } from '@supabase/supabase-js';

/**
 * Create a server-only Supabase admin client.
 *
 * The service-role key is intentionally not allowed to fall back to an anon
 * key. A fallback makes authorization failures look like data-layer failures
 * and encourages accidentally using a privileged client without privileges.
 */
export function getSupabaseAdmin(): SupabaseClient {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error('SUPABASE_SERVICE_ROLE_KEY is required for this server operation');
  }

  return createClient(supabaseUrl, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
