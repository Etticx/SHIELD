"use client";

// =============================================================================
// SHIELD — Account Settings  (/settings)
//
// A single-card "Profile & Security" settings page.
// All inputs are controlled local state — no backend calls yet.
// Two independent save flows:
//   • Save Changes  → profile section (full name, employee ID/role)
//   • Update Password → security section (current + new password)
// Both show inline success / error feedback without a page reload.
// =============================================================================

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import {
  User,
  Briefcase,
  Lock,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  Save,
  ShieldCheck,
} from "lucide-react";
import clsx from "clsx";

// ---------------------------------------------------------------------------
// Tiny helpers
// ---------------------------------------------------------------------------

function FieldLabel({
  htmlFor,
  children,
}: {
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className="block text-[0.68rem] font-bold uppercase tracking-[0.12em] text-brand-muted mb-1.5"
    >
      {children}
    </label>
  );
}

function HelperText({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-1.5 text-[0.68rem] text-brand-muted leading-relaxed">{children}</p>
  );
}

function SectionDivider({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-3 py-1">
      <span className="text-[0.68rem] font-bold uppercase tracking-[0.14em] text-brand-muted whitespace-nowrap">
        {title}
      </span>
      <div className="flex-1 h-px bg-brand-border" />
    </div>
  );
}

type FeedbackState = { type: "success" | "error"; message: string } | null;

function InlineFeedback({ fb }: { fb: FeedbackState }) {
  if (!fb) return null;
  const isSuccess = fb.type === "success";
  return (
    <div
      className={clsx(
        "flex items-center gap-2 px-3 py-2.5 rounded-md border text-xs",
        isSuccess
          ? "bg-[rgba(22,163,74,0.06)] border-[rgba(22,163,74,0.25)] text-[#166534]"
          : "bg-[rgba(220,38,38,0.05)] border-[rgba(220,38,38,0.2)] text-[#991B1B]"
      )}
    >
      {isSuccess ? <CheckCircle2 size={13} className="shrink-0" /> : <AlertCircle size={13} className="shrink-0" />}
      <span>{fb.message}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function SettingsPage() {
  const { user } = useAuth();

  // ── Profile state ──────────────────────────────────────────────────────────
  const [fullName,    setFullName]    = useState("Muhd Alif Asyraf bin Mohd Azlan");
  const [employeeRole, setEmployeeRole] = useState("AI Engineer");
  const [profileFb,  setProfileFb]   = useState<FeedbackState>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  // ── Security state ─────────────────────────────────────────────────────────
  const [currentPw, setCurrentPw] = useState("");
  const [newPw,     setNewPw]     = useState("");
  const [securityFb, setSecurityFb] = useState<FeedbackState>(null);
  const [savingPw,  setSavingPw]   = useState(false);

  // ── Handlers ───────────────────────────────────────────────────────────────
  function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!fullName.trim()) {
      setProfileFb({ type: "error", message: "Full name cannot be empty." });
      return;
    }
    setSavingProfile(true);
    setProfileFb(null);
    setTimeout(() => {
      setSavingProfile(false);
      setProfileFb({ type: "success", message: "Profile information updated successfully." });
    }, 700);
  }

  function handleUpdatePassword(e: React.FormEvent) {
    e.preventDefault();
    if (!currentPw || !newPw) {
      setSecurityFb({ type: "error", message: "Both password fields are required." });
      return;
    }
    if (newPw.length < 8) {
      setSecurityFb({ type: "error", message: "New password must be at least 8 characters." });
      return;
    }
    if (currentPw === newPw) {
      setSecurityFb({ type: "error", message: "New password must differ from the current password." });
      return;
    }
    setSavingPw(true);
    setSecurityFb(null);
    setTimeout(() => {
      setSavingPw(false);
      setCurrentPw("");
      setNewPw("");
      setSecurityFb({ type: "success", message: "Password updated. Changes take effect on next login." });
    }, 700);
  }

  return (
    <div className="min-h-screen bg-brand-cream">
      <div className="relative z-10 flex flex-col min-h-screen">

        {/* ── Page Header ──────────────────────────────────────────────────── */}
        <div className="px-6 pt-6 pb-5 border-b border-brand-border/60">
          <p className="section-label">Configuration</p>
          <h1 className="text-2xl font-bold text-brand-charcoal font-heading leading-tight">
            Account Settings
          </h1>
          <p className="text-sm text-brand-muted mt-1">
            Manage your profile information and security credentials.
          </p>
        </div>

        {/* ── Centred card ─────────────────────────────────────────────────── */}
        <div className="flex-1 px-6 py-8 flex justify-center">
          <div className="w-full max-w-2xl flex flex-col gap-6">

            {/* ── Who you're editing (read-only identity strip) ──────────── */}
            <div className="bg-brand-panel border border-brand-border rounded-md px-5 py-4
                            flex items-center gap-4">
              <div className="h-11 w-11 rounded-md bg-brand-charcoal flex items-center
                              justify-center shrink-0">
                <span className="font-mono font-bold text-lg text-brand-yellow">
                  {user?.username?.[0]?.toUpperCase() ?? "U"}
                </span>
              </div>
              <div>
                <p className="text-sm font-bold text-brand-charcoal font-heading leading-tight">
                  {user?.username}
                </p>
                <p className="text-[0.68rem] text-brand-muted mt-0.5 font-mono">
                  Authenticated session · Read-only identifier
                </p>
              </div>
              <div className="ml-auto flex items-center gap-1.5 text-[#16A34A]">
                <ShieldCheck size={13} />
                <span className="text-[0.68rem] font-semibold">Active</span>
              </div>
            </div>

            {/* ── Profile Information ────────────────────────────────────── */}
            <div className="bg-brand-panel border border-brand-border rounded-md overflow-hidden">

              <div className="px-5 pt-4 pb-3 border-b border-brand-border">
                <h2 className="text-sm font-bold text-brand-charcoal font-heading">
                  Profile Information
                </h2>
                <p className="text-[0.68rem] text-brand-muted mt-0.5">
                  Displayed on evaluation reports and internal records.
                </p>
              </div>

              <form onSubmit={handleSaveProfile} className="px-5 py-5 flex flex-col gap-5">

                <SectionDivider title="Identity" />

                {/* Full Name */}
                <div>
                  <FieldLabel htmlFor="full-name">Full Name</FieldLabel>
                  <div className="relative">
                    <User
                      size={13}
                      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"
                    />
                    <input
                      id="full-name"
                      type="text"
                      value={fullName}
                      onChange={(e) => { setFullName(e.target.value); setProfileFb(null); }}
                      placeholder="Muhd Alif Asyraf bin Mohd Azlan"
                      className="input-field pl-8"
                    />
                  </div>
                  <HelperText>
                    This name will appear as the Evaluator on official PDF reports.
                  </HelperText>
                </div>

                {/* Employee ID / Role */}
                <div>
                  <FieldLabel htmlFor="employee-role">Employee ID / Role</FieldLabel>
                  <div className="relative">
                    <Briefcase
                      size={13}
                      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"
                    />
                    <input
                      id="employee-role"
                      type="text"
                      value={employeeRole}
                      onChange={(e) => { setEmployeeRole(e.target.value); setProfileFb(null); }}
                      placeholder="AI Engineer"
                      className="input-field pl-8"
                    />
                  </div>
                </div>

                {/* Feedback */}
                <InlineFeedback fb={profileFb} />

                {/* Save */}
                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="btn-primary flex items-center gap-2 px-5 py-2.5 text-sm disabled:opacity-60"
                  >
                    {savingProfile ? (
                      <>
                        <svg className="animate-spin h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10"
                            stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        Saving…
                      </>
                    ) : (
                      <>
                        <Save size={13} />
                        Save Changes
                      </>
                    )}
                  </button>
                </div>

              </form>
            </div>

            {/* ── Security ──────────────────────────────────────────────── */}
            <div className="bg-brand-panel border border-brand-border rounded-md overflow-hidden">

              <div className="px-5 pt-4 pb-3 border-b border-brand-border">
                <h2 className="text-sm font-bold text-brand-charcoal font-heading">
                  Security
                </h2>
                <p className="text-[0.68rem] text-brand-muted mt-0.5">
                  Update your login credentials. Minimum 8 characters.
                </p>
              </div>

              <form onSubmit={handleUpdatePassword} className="px-5 py-5 flex flex-col gap-5">

                <SectionDivider title="Change Password" />

                {/* Current Password */}
                <div>
                  <FieldLabel htmlFor="current-pw">Current Password</FieldLabel>
                  <div className="relative">
                    <Lock
                      size={13}
                      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"
                    />
                    <input
                      id="current-pw"
                      type="password"
                      value={currentPw}
                      onChange={(e) => { setCurrentPw(e.target.value); setSecurityFb(null); }}
                      placeholder="Enter current password"
                      autoComplete="current-password"
                      className="input-field pl-8"
                    />
                  </div>
                </div>

                {/* New Password */}
                <div>
                  <FieldLabel htmlFor="new-pw">New Password</FieldLabel>
                  <div className="relative">
                    <KeyRound
                      size={13}
                      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"
                    />
                    <input
                      id="new-pw"
                      type="password"
                      value={newPw}
                      onChange={(e) => { setNewPw(e.target.value); setSecurityFb(null); }}
                      placeholder="Minimum 8 characters"
                      autoComplete="new-password"
                      className="input-field pl-8"
                    />
                  </div>

                  {/* Password strength micro-indicator */}
                  {newPw.length > 0 && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex gap-1">
                        {[1, 2, 3].map((level) => {
                          const strength = newPw.length < 8 ? 1 : newPw.length < 12 ? 2 : 3;
                          return (
                            <div
                              key={level}
                              className={clsx(
                                "h-1 w-8 rounded-sm transition-colors duration-200",
                                level <= strength
                                  ? strength === 1 ? "bg-[#DC2626]"
                                  : strength === 2 ? "bg-[#D97706]"
                                  : "bg-[#16A34A]"
                                  : "bg-brand-border"
                              )}
                            />
                          );
                        })}
                      </div>
                      <span className="text-[0.65rem] text-brand-muted">
                        {newPw.length < 8 ? "Weak" : newPw.length < 12 ? "Fair" : "Strong"}
                      </span>
                    </div>
                  )}
                </div>

                {/* Feedback */}
                <InlineFeedback fb={securityFb} />

                {/* Update Password button */}
                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={savingPw}
                    className={clsx(
                      "btn-ghost flex items-center gap-2 px-5 py-2.5 text-sm font-semibold",
                      "border border-brand-charcoal text-brand-charcoal",
                      "hover:bg-brand-charcoal hover:text-white transition-colors duration-150",
                      "disabled:opacity-50 disabled:cursor-not-allowed"
                    )}
                  >
                    {savingPw ? (
                      <>
                        <svg className="animate-spin h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10"
                            stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        Updating…
                      </>
                    ) : (
                      <>
                        <KeyRound size={13} />
                        Update Password
                      </>
                    )}
                  </button>
                </div>

              </form>
            </div>

            {/* ── Danger / session note ────────────────────────────────── */}
            <div className="border border-brand-border rounded-md px-5 py-4 bg-brand-panel">
              <p className="text-[0.68rem] text-brand-muted/80 leading-relaxed">
                <span className="font-bold text-brand-muted">Note:</span> Profile changes are
                session-scoped in this build. Password changes take effect on next login. For
                permanent account changes, contact your system administrator.
              </p>
            </div>

          </div>
        </div>

        {/* ── Footer ───────────────────────────────────────────────────────── */}
        <footer className="border-t border-brand-border px-6 py-3 flex items-center
                           justify-between text-brand-muted text-xs mt-auto">
          <span>SHIELD · Final Year Project · For academic use only</span>
          <span>JuneBank Internal Tools · XGBoost + SHAP</span>
        </footer>

      </div>
    </div>
  );
}
