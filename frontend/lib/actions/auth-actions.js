'use server';

import { redirect } from 'next/navigation';
import { createSupabaseClient } from '@/Clients/supabase/server';
import { cookies, headers } from 'next/headers';

//====== GOOGLE OAUTH SIGN IN ======//

export async function signInWithGoogle() {
  const supabase = await createSupabaseClient();

  const origin = (await headers()).get('origin');

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${origin}/api/auth/callback`,
      queryParams: {
        access_type: 'offline',
        prompt: 'consent',
        scope: [
          'openid',
          'email',
          'profile',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          // "https://www.googleapis.com/auth/gmail.send",
          // // YouTube permissions
          // "https://www.googleapis.com/auth/youtube.readonly",
          // "https://www.googleapis.com/auth/yt-analytics.readonly",
          // "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
          // "https://www.googleapis.com/auth/youtube.force-ssl"
        ].join(' '),
      },
    },
  });

  if (error) {
    console.error('Google OAuth Error:', error);
    redirect('/error');
  }

  console.log('Redirecting to:', data.url);
  redirect(data.url);
}

//====== USER SIGN OUT ======//

export async function signout() {
  const supabase = await createSupabaseClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    console.error('Logout Error:', error);
    redirect('/error');
  }

  (await cookies()).delete('user_data');
  (await cookies()).delete('fallback_user_data');
  (await cookies()).delete('user_session');

  redirect('/logout');
}
