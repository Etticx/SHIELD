"use client";

// =============================================================================
// SHIELD — AppShell
// Gates the app: login page → splash → dashboard.
//
// States:
//   not logged in              → LoginPage
//   logged in + splashPending  → SplashScreen (over the dashboard)
//   logged in + splash done    → Navbar + dashboard (children)
//
// On refresh while logged in: splashPending is false (in-memory, not persisted)
// so the dashboard shows immediately with no splash.
// =============================================================================

import { useAuth } from "@/lib/auth";
import SplashScreen from "@/components/SplashScreen";
import LoginPage from "@/components/LoginPage";
import Navbar from "@/components/Navbar";
import type { ReactNode } from "react";

export default function AppShell({ children }: { children: ReactNode }) {
  const { isLoggedIn, splashPending } = useAuth();

  // ---- Not logged in → show login page only ----
  if (!isLoggedIn) {
    return <LoginPage />;
  }

  // ---- Logged in + splash needs to play ----
  // Render the dashboard underneath so it's ready the moment splash fades.
  if (splashPending) {
    return (
      <>
        <SplashScreen />
        {/* Dashboard pre-rendered beneath the splash */}
        <Navbar />
        <div className="pt-16">{children}</div>
      </>
    );
  }

  // ---- Logged in + no splash ----
  return (
    <>
      <Navbar />
      <div className="pt-16">{children}</div>
    </>
  );
}
