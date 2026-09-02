"use client";

// =============================================================================
// SHIELD — AuthContext
//
// Splash behaviour:
//   - Splash plays AFTER a successful login action (not on page load/refresh).
//   - On refresh while already logged in → no splash, go straight to dashboard.
//   - On logout → login page shown, no splash.
//   - On re-login → splash plays again, then dashboard.
//
// Implementation:
//   - `isLoggedIn` is persisted in sessionStorage (survives refresh).
//   - `splashPending` is pure in-memory state (does NOT survive refresh).
//     It is set to true by login(), cleared by markSplashDone().
// =============================================================================

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";

const SESSION_KEY = "shield_auth";

interface AuthUser {
  username: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoggedIn: boolean;
  splashPending: boolean;       // true = splash needs to play right now
  markSplashDone: () => void;   // call when splash finishes
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Hard-coded demo credentials — edit here to change users
// ---------------------------------------------------------------------------
const DEMO_USERS: Record<string, string> = {
  admin: "admin",
  analyst: "junebank1",
};

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [splashPending, setSplashPending] = useState(false); // in-memory only
  const [hydrated, setHydrated] = useState(false);

  // Rehydrate login state from sessionStorage on mount.
  // splashPending stays false on refresh — intentional.
  useEffect(() => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch { /* ignore corrupt data */ }
    }
    setHydrated(true);
  }, []);

  const markSplashDone = useCallback(() => {
    setSplashPending(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const expected = DEMO_USERS[username.toLowerCase()];
    if (!expected || expected !== password) {
      throw new Error("Invalid username or password.");
    }
    const u: AuthUser = { username };
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(u));
    setUser(u);
    setSplashPending(true); // trigger splash after this login
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem("shield_workspace"); // clear active workspace on logout
    setSplashPending(false);
    setUser(null);
  }, []);

  if (!hydrated) return null;

  return (
    <AuthContext.Provider
      value={{ user, isLoggedIn: !!user, splashPending, markSplashDone, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
