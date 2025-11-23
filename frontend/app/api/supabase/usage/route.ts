import { getSupabaseAdmin } from '@/lib/supabase/admin';
import { createSupabaseClient } from '@/Clients/supabase/server';
import { rateLimit } from '@/lib/rateLimit';
import { NextResponse, NextRequest } from 'next/server';
import { UsageRequest } from '../models/api';

const limiter = rateLimit(10, 60000);

export async function POST(request: NextRequest) {
  try {
    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    if (!limiter.check(ip)) {
      return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
    }

    const body: UsageRequest = await request.json();
    const { userId, apiKeyId, from, to } = body;

    if (!userId) {
      return NextResponse.json({ error: 'Missing userId' }, { status: 400 });
    }

    // Server-side auth verification
    const supabase = await createSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user || user.id !== userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    let query = getSupabaseAdmin()
      .from('usage')
      .select('*')
      .eq('user_id', userId)
      .order('timestamp', { ascending: true });

    if (apiKeyId) query = query.eq('api_token_id', apiKeyId);
    if (from) query = query.gte('timestamp', from);
    if (to) query = query.lte('timestamp', to);

    const { data, error } = await query;

    if (error) throw error;

    return NextResponse.json({ data });
  } catch (error) {
    console.error('Error fetching usage:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
