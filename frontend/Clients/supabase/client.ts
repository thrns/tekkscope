//====== SUPABASE BROWSER CLIENT ======//

import { createBrowserClient } from '@supabase/ssr';

//====== CLIENT CREATION ======//

export function createSupabaseClient() {
  // Create the Supabase client with proper configuration
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

//====== CLIENT INSTANCE ======//

export const supabase = createSupabaseClient();
