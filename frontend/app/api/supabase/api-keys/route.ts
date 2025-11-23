import { createHash, randomUUID } from 'node:crypto';
import { getSupabaseAdmin } from '@/lib/supabase/admin';
import { createSupabaseClient } from '@/Clients/supabase/server';
import { rateLimit } from '@/lib/rateLimit';
import { NextResponse, NextRequest } from 'next/server';

const readLimiter = rateLimit(10, 60000);
const writeLimiter = rateLimit(5, 60000);

function requestIp(request: NextRequest) {
  return request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
}

function maskKey(value: string | null | undefined) {
  if (!value) return value;
  return `${value.slice(0, 10)}...${value.slice(-4)}`;
}

async function authenticatedUser() {
  const supabase = await createSupabaseClient();
  const { data, error } = await supabase.auth.getUser();
  if (error || !data.user) return null;
  return data.user;
}

async function listForUser(userId: string) {
  const admin = getSupabaseAdmin();
  try {
    const { data, error } = await admin
      .from('api_keys')
      .select('id, api_key_prefix, api_key_name, created_at, created_by')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });
    if (!error) {
      return (data || []).map((row) => ({
        ...row,
        // Keep the existing table contract while exposing only a prefix.
        api_key: row.api_key_prefix || 'ts_????????',
      }));
    }
  } catch {
    // Fall back for legacy installations without api_key_prefix.
  }

  const { data, error } = await admin
    .from('api_keys')
    .select('id, api_key, api_key_name, created_at, created_by')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });
  if (error) throw error;
  return (data || []).map((row) => ({
    ...row,
    api_key: maskKey(row.api_key),
  }));
}

export async function GET(request: NextRequest) {
  try {
    if (!readLimiter.check(requestIp(request))) {
      return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
    }
    const user = await authenticatedUser();
    if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    return NextResponse.json({ data: await listForUser(user.id) });
  } catch (error) {
    console.error('Error fetching API keys:', error instanceof Error ? error.message : 'unknown');
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

// POST remains supported for the existing dashboard client. With a name it
// creates a key; without one it behaves like the old list operation.
export async function POST(request: NextRequest) {
  try {
    const user = await authenticatedUser();
    if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const body = await request.json().catch(() => ({}));
    if (!body?.name) {
      if (!readLimiter.check(requestIp(request))) {
        return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
      }
      return NextResponse.json({ data: await listForUser(user.id) });
    }

    if (!writeLimiter.check(requestIp(request))) {
      return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
    }

    const apiKey = `ts_${randomUUID().replaceAll('-', '')}`;
    const hash = createHash('sha256').update(`${process.env.TEKK_API_KEY_PEPPER || ''}:${apiKey}`).digest('hex');
    const admin = getSupabaseAdmin();
    const securePayload = {
      user_id: user.id,
      api_key_hash: hash,
      api_key_prefix: apiKey.slice(0, 10),
      api_key_name: String(body.name).trim().slice(0, 100) || 'Untitled key',
      created_by: user.email || user.id,
    };

    let { data, error } = await admin.from('api_keys').insert(securePayload).select('id').single();
    if (error) {
      // Preserve compatibility until the database migration is applied.
      ({ data, error } = await admin.from('api_keys').insert({
        user_id: user.id,
        api_key: apiKey,
        api_key_name: securePayload.api_key_name,
        created_by: securePayload.created_by,
      }).select('id').single());
    }
    if (error) throw error;
    return NextResponse.json({ api_key: apiKey, id: data?.id });
  } catch (error) {
    console.error('Error creating API key:', error instanceof Error ? error.message : 'unknown');
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    if (!writeLimiter.check(requestIp(request))) {
      return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
    }
    const user = await authenticatedUser();
    if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const id = new URL(request.url).searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'Missing API Key ID' }, { status: 400 });

    const { data, error } = await getSupabaseAdmin()
      .from('api_keys')
      .delete()
      .eq('id', id)
      .eq('user_id', user.id)
      .select('id');
    if (error) throw error;
    if (!data?.length) return NextResponse.json({ error: 'Key not found' }, { status: 404 });
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting API key:', error instanceof Error ? error.message : 'unknown');
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
