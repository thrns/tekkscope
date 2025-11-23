import { createSupabaseClient } from "@/Clients/supabase/server";
import { NextResponse } from "next/server";

export async function GET(request) {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    const requestedNext = searchParams.get("next") ?? "/";
    // Only allow same-origin relative redirects. This keeps the callback
    // compatible with deep links without creating an open redirect.
    const next = requestedNext.startsWith("/") && !requestedNext.startsWith("//")
        ? requestedNext
        : "/";

    if (code) {
        const supabase = await createSupabaseClient();
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (!error) {
            return NextResponse.redirect(new URL(next, request.url));
        }
    }

    return NextResponse.redirect(new URL("/auth/auth-code-error", request.url));
}
