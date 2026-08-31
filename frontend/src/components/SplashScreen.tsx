"use client";

// =============================================================================
// SHIELD — SplashScreen
// Appears instantly on top of the dashboard (opacity 1 from the start).
// After MAX_DURATION ms, fades out smoothly to reveal the dashboard.
// =============================================================================

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth";

const MAX_DURATION = 2000; // ms — how long the splash stays fully visible
const FADE_OUT_MS = 600;  // ms — fade out to dashboard

export default function SplashScreen() {
  const { markSplashDone } = useAuth();
  const [fading, setFading] = useState(false);
  const [done, setDone] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const startFadeOut = useCallback(() => {
    setFading(true);
    const t = setTimeout(() => {
      setDone(true);
      markSplashDone();
    }, FADE_OUT_MS);
    return () => clearTimeout(t);
  }, [markSplashDone]);

  useEffect(() => {
    const t = setTimeout(startFadeOut, MAX_DURATION);
    return () => clearTimeout(t);
  }, [startFadeOut]);

  if (done) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        backgroundColor: "#0e1117",
        opacity: fading ? 0 : 1,
        transition: fading ? `opacity ${FADE_OUT_MS}ms ease` : "none",
        pointerEvents: fading ? "none" : "auto",
      }}
    >
      <video
        ref={videoRef}
        src="/JuneBankLoading.mp4"
        autoPlay
        muted
        playsInline
        style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
      />
    </div>
  );
}
