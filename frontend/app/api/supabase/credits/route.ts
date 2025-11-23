import { getSupabaseAdmin } from '@/lib/supabase/admin';
import { createSupabaseClient } from '@/Clients/supabase/server';
import { rateLimit } from '@/lib/rateLimit';
import { NextResponse, NextRequest } from 'next/server';
import { CreditsRequest } from '../models/api';

const limiter = rateLimit(20, 60000); // Higher limit for credits check

export async function POST(request: NextRequest) {
  try {
    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    if (!limiter.check(ip)) {
      return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
    }

    const body: CreditsRequest = await request.json();
    const { userId } = body;

    if (!userId) {
      return NextResponse.json({ error: 'Missing userId' }, { status: 400 });
    }

    // Server-side auth verification
    const supabase = await createSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user || user.id !== userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { data, error } = await getSupabaseAdmin()
      .from('credits')
      .select('balance,last_updated')
      .eq('user_id', userId)
      .maybeSingle();

    if (error) throw error;

    return NextResponse.json({ data });
  } catch (error) {
    console.error('Error fetching credits:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
