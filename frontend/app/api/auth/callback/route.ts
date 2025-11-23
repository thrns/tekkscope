import { createSupabaseClient } from '@/Clients/supabase/server';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { storeUserDataServer } from '@/lib/utils/sessionUtils';
import { JSONValue } from 'next/dist/server/config-shared';

export async function GET(request: Request) {
  //======== SETUP =========//
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const appUrl: string =
    process.env.NODE_ENV == 'production'
      ? process.env.NEXT_PUBLIC_DOMAIN || ''
      : requestUrl.origin || '';

  if (!code) {
    return NextResponse.redirect(appUrl);
  }

  //======== SESSION EXCHANGE =========//
  const supabase = await createSupabaseClient();
  const { data: sessionData, error: sessionError } =
    await supabase.auth.exchangeCodeForSession(code);

  if (sessionError) {
    console.error(
      '❌ Error exchanging code for session:',
      sessionError.message
    );
    return NextResponse.redirect(`${appUrl}/error`);
  }

  const supabaseUser = sessionData.user;
  if (!supabaseUser) {
    console.error('❌ No Supabase user found after session exchange.');
    return NextResponse.redirect(`${appUrl}/error`);
  }

  //======== FETCH USER DATA =========//
  const { data: userData, error: userError } = await supabase
    .from('user_data')
    .select('*')
    .eq('email', supabaseUser.email)
    .single();

  let user = userData;

  if (userError && userError.code !== 'PGRST116') {
    console.error('❌ Error fetching user data:', userError);
    return NextResponse.redirect(`${appUrl}/error`);
  }

  const session = sessionData.session;

  if (!user) {
    //======== NEW USER =========//
    const newUser = {
      name: supabaseUser.user_metadata.full_name || null,
      email: supabaseUser.email || null,
      avatarURL: supabaseUser.user_metadata.avatar_url || null,
      integrations: {
        googleRefreshToken: session?.provider_refresh_token || null,
      },
      uuid: supabaseUser.id,
      onboarding: false,
      loggedin_at: new Date().toISOString(),
    };

    const { data: insertedUser, error: insertError } = await supabase
      .from('user_data')
      .insert(newUser)
      .select()
      .single();

    if (insertError) {
      console.error('❌ Error inserting new user:', insertError);
      return NextResponse.redirect(`${appUrl}/error`);
    }
    user = insertedUser;
  } else {
    //======== EXISTING USER =========//
    const updatePayload: {
      loggedin_at: string;
      integrations: JSONValue;
    } = {
      loggedin_at: new Date().toISOString(),
      integrations: JSON.stringify({
        googleRefreshToken: session?.provider_refresh_token,
      }),
    };

    const { data: updatedUser, error: updateErr } = await supabase
      .from('user_data')
      .update(updatePayload)
      .eq('uuid', user.uuid)
      .select()
      .single();

    if (updateErr) {
      console.error('❌ Error updating user data:', updateErr);
      // Continue with stale user data
    } else {
      user = updatedUser;
    }
  }

  //======== STORE SESSION & REDIRECT =========//
  if (user) {
    await storeUserDataServer(user, await cookies());
  }

  if (user && !user.onboarding) {
    return NextResponse.redirect(`${appUrl}/onboarding`);
  }

  return NextResponse.redirect(`${appUrl}/dashboard`);
}

