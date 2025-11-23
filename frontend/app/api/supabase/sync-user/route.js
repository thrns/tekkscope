import { getSupabaseAdmin } from '@/lib/supabase/admin';
import { createSupabaseClient } from '@/Clients/supabase/server';
import { rateLimit } from '@/lib/rateLimit';
import { NextResponse } from 'next/server';

// Initialize rate limiter: 5 requests per minute per IP
const limiter = rateLimit(5, 60000);

export async function POST(request) {
  try {
    // 1. Rate Limiting
    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    if (!limiter.check(ip)) {
      return NextResponse.json(
        { error: 'Too many requests' },
        { status: 429 }
      );
    }

    // 2. Authenticate the caller before accepting identity fields.
    const sessionClient = await createSupabaseClient();
    const { data: authData, error: authError } = await sessionClient.auth.getUser();
    if (authError || !authData.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { email, authId } = body;

    if (!email || !authId || authId !== authData.user.id || email !== authData.user.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const supabase = getSupabaseAdmin();

    // 3. Secure Database Operation
    // We only update the UUID if it doesn't match, similar to the original frontend logic
    // but now it's done securely on the server.
    
    // First, fetch the user to check
    const { data: userData, error: fetchError } = await supabase
      .from('user_data')
      .select('uuid, email')
      .eq('email', email)
      .single();

    if (fetchError) {
      console.error('Error fetching user for sync:', fetchError);
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    // If UUIDs don't match, update it
    if (userData.uuid !== authId) {
      const { error: updateError } = await supabase
        .from('user_data')
        .update({ uuid: authId })
        .eq('email', email);

      if (updateError) {
        console.error('Error updating authId:', updateError);
        return NextResponse.json(
          { error: 'Failed to sync user' },
          { status: 500 }
        );
      }
      
      return NextResponse.json({ 
        message: 'User synced successfully', 
        synced: true 
      });
    }

    return NextResponse.json({ 
      message: 'User already in sync', 
      synced: false 
    });

  } catch (error) {
    console.error('Sync API Error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
