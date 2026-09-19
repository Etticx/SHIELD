"use client";

// =============================================================================
// SHIELD — LoginPage Component
// JuneBank corporate login screen with eagle watermark background.
// =============================================================================

import { useState, useCallback } from "react";
import Image from "next/image";
import { X, AlertTriangle } from "lucide-react";
import { useAuth } from "@/lib/auth";

// ---------------------------------------------------------------------------
// Help Modal
// ---------------------------------------------------------------------------
function HelpModal({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.45)", backdropFilter: "blur(4px)" }}
      onClick={onClose}
    >
      <div
        className="bg-brand-panel rounded-2xl shadow-card w-full max-w-md p-8 flex flex-col gap-6 animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] uppercase tracking-widest text-brand-muted font-semibold mb-1">
              Support
            </p>
            <h2 className="text-lg font-bold text-brand-charcoal font-heading">
              Account Help
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-brand-muted hover:text-brand-charcoal transition-colors mt-0.5 p-0.5 rounded"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="h-px bg-brand-border" />

        {/* Item 1 — Access Request */}
        <div className="flex gap-4">
          <div className="shrink-0 w-9 h-9 rounded-full bg-brand-yellow/20 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1A1A1A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-brand-charcoal mb-1">New Access Request</p>
            <p className="text-sm text-brand-muted leading-relaxed">
              For system access, please refer to your superior{" "}
              <span className="font-semibold text-brand-charcoal">(Manager and above)</span> to
              submit an access request on your behalf.
            </p>
          </div>
        </div>

        <div className="h-px bg-brand-border" />

        {/* Item 2 — Forgot Password */}
        <div className="flex gap-4">
          <div className="shrink-0 w-9 h-9 rounded-full bg-brand-yellow/20 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1A1A1A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-brand-charcoal mb-1">Forgotten Password</p>
            <p className="text-sm text-brand-muted leading-relaxed">
              If you have forgotten your password, please{" "}
              <button
                className="text-brand-charcoal font-semibold underline underline-offset-2 hover:text-brand-yellow transition-colors"
                onClick={() => alert("Password reset flow coming soon.")}
              >
                click here to reset your password
              </button>
              . You will be asked to verify your registered email address.
            </p>
          </div>
        </div>

        <div className="h-px bg-brand-border" />

        <p className="text-[11px] text-brand-muted text-center">
          JuneBank IT Support &nbsp;·&nbsp; Internal Use Only
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// LoginPage
// ---------------------------------------------------------------------------
export default function LoginPage() {
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      if (!username.trim() || !password) {
        setError("Please enter your username and password.");
        return;
      }
      setLoading(true);
      try {
        await login(username.trim(), password);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed.");
      } finally {
        setLoading(false);
      }
    },
    [username, password, login]
  );

  return (
    <>
      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}

      {/* Full-page cream background */}
      <div className="min-h-screen bg-brand-cream flex flex-col relative overflow-hidden">

        {/* ---- Eagle watermark — same treatment as the dashboard ---- */}
        <div
          aria-hidden="true"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            pointerEvents: "none",
            userSelect: "none",
          }}
        >
          <Image
            src="/JuneBankEagle.png"
            alt=""
            width={780}
            height={780}
            priority
            style={{
              opacity: 0.06,
              filter: "grayscale(1) contrast(0.8)",
              pointerEvents: "none",
              userSelect: "none",
            }}
          />
        </div>

        {/* ---- All content above the watermark ---- */}
        <div className="relative flex flex-col min-h-screen" style={{ zIndex: 1 }}>

          {/* ---- Top bar ---- */}
          <div className="w-full border-b border-brand-border bg-brand-panel/80 px-8 py-4 flex items-center justify-between backdrop-blur-sm">
            <Image
              src="/JuneBank.png"
              alt="JuneBank"
              width={148}
              height={40}
              priority
              style={{ objectFit: "contain" }}
            />
            <span className="text-[11px] text-brand-muted font-medium tracking-wide uppercase">
              Internal Systems Portal
            </span>
          </div>

          {/* ---- Login card ---- */}
          <div className="flex-1 flex items-center justify-center px-4 py-12">
            <div className="w-full max-w-sm">

              <div className="bg-brand-panel rounded-2xl shadow-card border border-brand-border overflow-hidden">

                {/* Yellow accent bar */}
                <div className="h-1 w-full bg-brand-yellow" />

                <div className="px-8 py-8 flex flex-col gap-6">

                  {/* Heading */}
                  <div className="flex flex-col gap-1">
                    <p className="text-[11px] uppercase tracking-widest text-brand-muted font-semibold">
                      SHIELD — Risk Evaluation Platform
                    </p>
                    <h1 className="text-2xl font-bold text-brand-charcoal font-heading">
                      Sign In
                    </h1>
                    <p className="text-sm text-brand-muted">
                      Use your JuneBank credentials to continue.
                    </p>
                  </div>

                  {/* Error banner */}
                  {error && (
                    <div className="px-3 py-2.5 bg-risk-highBg border border-risk-high/30 rounded-lg
                                    text-risk-high text-sm flex items-center gap-2">
                      <AlertTriangle size={14} />
                      <span>{error}</span>
                    </div>
                  )}

                  {/* Form */}
                  <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>

                    {/* Username */}
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="username" className="text-xs font-semibold text-brand-charcoal uppercase tracking-wide">
                        Username
                      </label>
                      <input
                        id="username"
                        type="text"
                        autoComplete="username"
                        autoFocus
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="e.g. jsmith"
                        className="w-full bg-brand-cream border border-brand-border rounded-lg
                                   px-3.5 py-2.5 text-sm text-brand-charcoal placeholder:text-brand-subtext
                                   focus:outline-none focus:ring-2 focus:ring-brand-yellow/50
                                   focus:border-brand-yellow transition-colors"
                      />
                    </div>

                    {/* Password */}
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="password" className="text-xs font-semibold text-brand-charcoal uppercase tracking-wide">
                        Password
                      </label>
                      <div className="relative">
                        <input
                          id="password"
                          type={showPw ? "text" : "password"}
                          autoComplete="current-password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="••••••••"
                          className="w-full bg-brand-cream border border-brand-border rounded-lg
                                     px-3.5 py-2.5 pr-10 text-sm text-brand-charcoal placeholder:text-brand-subtext
                                     focus:outline-none focus:ring-2 focus:ring-brand-yellow/50
                                     focus:border-brand-yellow transition-colors"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPw((v) => !v)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-muted
                                     hover:text-brand-charcoal transition-colors text-xs font-medium"
                          tabIndex={-1}
                          aria-label={showPw ? "Hide password" : "Show password"}
                        >
                          {showPw ? "Hide" : "Show"}
                        </button>
                      </div>
                    </div>

                    {/* Submit */}
                    <button
                      type="submit"
                      disabled={loading}
                      className="mt-1 w-full bg-brand-yellow hover:bg-brand-yellowHover
                                 text-brand-charcoal font-bold text-sm rounded-lg
                                 px-4 py-3 transition-colors duration-200
                                 disabled:opacity-60 disabled:cursor-not-allowed
                                 flex items-center justify-center gap-2"
                    >
                      {loading ? (
                        <>
                          <span className="h-4 w-4 rounded-full border-2 border-brand-charcoal/30
                                           border-t-brand-charcoal animate-spin" />
                          Signing in…
                        </>
                      ) : (
                        "Sign In"
                      )}
                    </button>

                  </form>

                  {/* Help link */}
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={() => setShowHelp(true)}
                      className="text-xs text-brand-muted hover:text-brand-charcoal
                                 underline underline-offset-2 transition-colors"
                    >
                      Need help with access or password?
                    </button>
                  </div>

                </div>
              </div>

              {/* Footer note */}
              <p className="mt-5 text-center text-[11px] text-brand-muted">
                Authorised personnel only &nbsp;·&nbsp; JuneBank Internal Tools &nbsp;·&nbsp; For academic use only
              </p>

            </div>
          </div>

        </div>{/* end z-1 content wrapper */}
      </div>
    </>
  );
}
