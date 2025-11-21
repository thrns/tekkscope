// sessionUtils.ts - Utility functions for managing user sessions
import { UserData, SessionData } from './models/session';

/**
 * Creates a minimal session object with only essential fields for cookies
 * This prevents HTTP 431 errors caused by large cookie sizes
 */
export function createMinimalSession(userData: UserData): SessionData | null {
  if (!userData) return null;

  return {
    uuid: userData.uuid,
    email: userData.email,
    onboarding: userData.onboarding,
    name: userData.name,
    avatarURL: userData.avatarURL,
    loggedin_at: userData.loggedin_at,
  };
}

/**
 * Stores user data using a hybrid approach:
 * - Full user data in localStorage (client-side only)
 * - Minimal session data in cookies (for SSR and auth checks)
 */
export function storeUserData(userData: UserData, Cookies: any) {
  if (!userData) return;

  // Store full user data in localStorage (client-side only)
  if (typeof window !== "undefined") {
    localStorage.setItem("user", JSON.stringify(userData));
  }

  // Store minimal session data in cookies
  const minimalSession = createMinimalSession(userData);
  if (minimalSession) {
    Cookies.set("user_session", JSON.stringify(minimalSession), {
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
    });
  }
}

/**
 * Server-side version of storeUserData for Next.js API routes
 * Uses Next.js cookies() API instead of js-cookie
 */
export async function storeUserDataServer(userData: UserData, cookiesInstance: any) {
  if (!userData) return;

  // Store minimal session data in cookies
  const minimalSession = createMinimalSession(userData);
  if (minimalSession) {
    cookiesInstance.set("user_session", JSON.stringify(minimalSession), {
      httpOnly: false,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });
  }
}

/**
 * Retrieves user data using the hybrid approach:
 * - Tries localStorage first (full data)
 * - Falls back to cookies (minimal session data)
 * - Returns null if neither is available
 */
export function getUserData(Cookies: any): UserData | null {
  // Try localStorage first (client-side only)
  if (typeof window !== "undefined") {
    const localUser = localStorage.getItem("user");
    if (localUser) {
      try {
        return JSON.parse(localUser);
      } catch (error) {
        console.error("Error parsing localStorage user data:", error);
        localStorage.removeItem("user");
      }
    }
  }

  // Fall back to new user_session cookie (minimal session data)
  const sessionData = Cookies.get("user_session");

  if (sessionData) {
    try {
      return JSON.parse(sessionData);
    } catch {
      try {
        const decoded = decodeURIComponent(sessionData);
        return JSON.parse(decoded);
      } catch {
        // Ignore malformed client-side state. The Supabase session remains the
        // source of truth and will repopulate this cache after a refresh.
      }
    }
  }

  // Fall back to legacy cookies
  const legacyData = Cookies.get("user_data") || Cookies.get("fallback_user_data");
  if (legacyData) {
    try {
      return JSON.parse(legacyData);
    } catch {
      // Ignore malformed legacy state and let the authenticated session win.
    }
  }

  return null;
}

/**
 * Clears all user data from both localStorage and cookies
 */
export function clearUserData(Cookies: any) {
  // Clear localStorage
  if (typeof window !== "undefined") {
    localStorage.removeItem("user");
  }

  // Clear cookies
  Cookies.remove("user_session");
  Cookies.remove("user_data"); // Legacy cookie
  Cookies.remove("fallback_user_data"); // Legacy cookie
}

/**
 * Updates user data in both localStorage and cookies
 */
export function updateUserData(updatedUserData: UserData, Cookies: any) {
  storeUserData(updatedUserData, Cookies);
}
