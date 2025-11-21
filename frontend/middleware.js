// middleware.js
import { NextResponse } from 'next/server';
import { updateSession } from './Clients/supabase/middleware';

export default async function middleware(req) {
  try {
    const { pathname } = req.nextUrl;
    const origin = req.headers.get('origin') || '*';

    // =================== Handle CORS for API routes =================== //
    if (pathname.startsWith('/api')) {
      const allowedOrigins = [
        'http://localhost:3000',
        'https://tekkscope.com',
        'https://www.tekkscope.com',
        'https://api.tekkscope.com'
      ];
      
      const origin = req.headers.get('origin');
      const isAllowed = allowedOrigins.includes(origin) || !origin; // Allow non-browser requests (no origin) if needed, or strict check

      const headers = new Headers();
      
      if (isAllowed && origin) {
        headers.set('Access-Control-Allow-Origin', origin);
      }
      
      headers.set(
        'Access-Control-Allow-Methods',
        'GET, POST, PUT, DELETE, OPTIONS'
      );
      headers.set(
        'Access-Control-Allow-Headers',
        'Content-Type, Authorization, x-api-key'
      );
      headers.set('Access-Control-Allow-Credentials', 'true');

      if (req.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers });
      }

      const response = NextResponse.next();
      headers.forEach((value, key) => response.headers.set(key, value));
      return response;
    }

    // =================== PROTECT /dashboard and /onboarding routes =================== //
    try {
      const authResponse = await updateSession(req);

      if (authResponse.status === 307) {
        return authResponse;
      }
    } catch (authError) {
      console.error('Auth middleware error:', authError);
    }

   
    return NextResponse.next();
  } catch (error) {
    console.error('Global middleware error:', error);
    // Return a regular response instead of crashing
    return NextResponse.next();
  }
}

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
};
