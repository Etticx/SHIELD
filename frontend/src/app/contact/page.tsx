"use client";

// =============================================================================
// SHIELD — Internal System Support & Directory  (/contact)
// =============================================================================

import { useState } from "react";
import {
  User,
  Phone,
  Mail,
  BadgeCheck,
  Building2,
  TicketSlash,
  AlertCircle,
  ChevronDown,
  SendHorizonal,
  CheckCircle2,
  RotateCcw,
} from "lucide-react";
import clsx from "clsx";

// ---------------------------------------------------------------------------
// Static data
// ---------------------------------------------------------------------------
const PIC = {
  name: "Muhd Alif Asyraf bin Mohd Azlan",
  role: "Lead AI Architect, SHIELD Project",
  ext: "+60 3-5544 2000  (ext. 8492)",
  email: "alif.asyraf@junebank.internal.my",
};

const ISSUE_TYPES = [
  { value: "", label: "Select issue type…" },
  { value: "bug", label: "Bug Report" },
  { value: "model", label: "Model Hallucination" },
  { value: "access", label: "Access Request" },
];

const PRIORITIES = [
  { value: "", label: "Select priority…" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FieldLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label
      htmlFor={htmlFor}
      className="block text-[0.68rem] font-bold uppercase tracking-[0.12em] text-brand-muted mb-1.5"
    >
      {children}
    </label>
  );
}

function SelectField({
  id,
  value,
  onChange,
  options,
  required,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  required?: boolean;
}) {
  return (
    <div className="relative">
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        className={clsx(
          "w-full appearance-none bg-white border border-brand-border rounded-md",
          "px-3 py-2 pr-8 text-sm font-mono text-brand-charcoal",
          "focus:outline-none focus:ring-2 focus:ring-brand-yellow/40 focus:border-brand-yellow",
          "transition-colors",
          !value && "text-brand-muted"
        )}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value} disabled={o.value === ""}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown
        size={13}
        className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-brand-muted"
      />
    </div>
  );
}

function ContactRow({
  icon,
  label,
  value,
  mono = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-3 px-5 py-4">
      <div className="mt-0.5 shrink-0 text-brand-muted">{icon}</div>
      <div className="min-w-0">
        <p className="text-[0.65rem] font-bold uppercase tracking-[0.12em] text-brand-muted mb-0.5">
          {label}
        </p>
        <p className={clsx("text-sm text-brand-charcoal leading-snug break-all", mono && "font-mono text-[0.82rem]")}>
          {value}
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function ContactPage() {
  const [issueType, setIssueType] = useState("");
  const [priority, setPriority] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setTimeout(() => {
      const id = `JB-SHIELD-${Date.now().toString(36).toUpperCase()}`;
      setTicketId(id);
      setSubmitting(false);
      setSubmitted(true);
    }, 900);
  }

  function handleReset() {
    setIssueType("");
    setPriority("");
    setDescription("");
    setTicketId("");
    setSubmitted(false);
  }

  return (
    <div className="min-h-screen bg-brand-cream">
      <div className="relative z-10 flex flex-col min-h-screen">

        {/* ── Page Header ──────────────────────────────────────────────────── */}
        <div className="px-6 pt-6 pb-5 border-b border-brand-border/60">
          <p className="section-label">Help &amp; Support</p>
          <h1 className="text-2xl font-bold text-brand-charcoal font-heading leading-tight">
            Internal System Support
          </h1>
          <p className="text-sm text-brand-muted mt-1">
            JuneBank SHIELD Technical Assistance &amp; Directory
          </p>
        </div>

        {/* ── Body ─────────────────────────────────────────────────────────── */}
        <div className="flex-1 px-6 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">

            {/* ── LEFT: Support Ticket Form ─────────────────────────────── */}
            <div className="bg-brand-panel border border-brand-border rounded-md overflow-hidden">

              {/* Panel header — always visible */}
              <div className="px-5 pt-4 pb-3 border-b border-brand-border flex items-center gap-2.5">
                <TicketSlash size={14} className="text-brand-muted shrink-0" />
                <div>
                  <h2 className="text-sm font-bold text-brand-charcoal font-heading">
                    Submit a Support Ticket
                  </h2>
                  <p className="text-[0.68rem] text-brand-muted mt-0.5">
                    Tickets are routed to the JuneBank IT Support queue.
                  </p>
                </div>
              </div>

              {/* ── Success confirmation ── */}
              {submitted ? (
                <div className="px-5 py-10 flex flex-col items-center text-center gap-5">

                  {/* Green check icon */}
                  <div className="h-14 w-14 rounded-md border border-[rgba(22,163,74,0.3)]
                                  bg-[rgba(22,163,74,0.07)] flex items-center justify-center">
                    <CheckCircle2 size={28} className="text-[#16A34A]" />
                  </div>

                  <div>
                    <p className="text-base font-bold text-brand-charcoal font-heading">
                      Ticket Submitted Successfully
                    </p>
                    <p className="text-xs text-brand-muted mt-1.5 max-w-xs leading-relaxed">
                      Your request has been logged and routed to the JuneBank IT Support queue.
                      Expected response within{" "}
                      <span className="font-semibold text-brand-charcoal">1–2 business days</span>.
                    </p>
                  </div>

                  {/* Ticket reference box */}
                  <div className="w-full bg-brand-cream border border-brand-border rounded-md px-4 py-3 text-left">
                    <p className="text-[0.65rem] font-bold uppercase tracking-[0.13em] text-brand-muted mb-1">
                      Ticket Reference
                    </p>
                    <p className="font-mono text-sm font-bold text-brand-charcoal tracking-widest">
                      {ticketId}
                    </p>
                  </div>

                  {/* Summary of submission */}
                  <div className="w-full border border-brand-border rounded-md overflow-hidden text-left">
                    {[
                      { label: "Issue Type", value: ISSUE_TYPES.find((o) => o.value === issueType)?.label ?? issueType },
                      { label: "Priority", value: PRIORITIES.find((o) => o.value === priority)?.label ?? priority },
                    ].map(({ label, value }, i) => (
                      <div
                        key={label}
                        className={clsx(
                          "flex items-center justify-between px-4 py-2.5",
                          i > 0 && "border-t border-brand-border"
                        )}
                      >
                        <span className="text-[0.68rem] font-bold uppercase tracking-[0.1em] text-brand-muted">
                          {label}
                        </span>
                        <span className="text-xs font-semibold text-brand-charcoal font-mono">
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Reset link */}
                  <button
                    onClick={handleReset}
                    className="btn-ghost flex items-center gap-1.5 px-4 py-2 text-sm w-full justify-center mt-1"
                  >
                    <RotateCcw size={12} />
                    Submit another ticket
                  </button>

                </div>

              ) : (
                /* ── Form ── */
                <form onSubmit={handleSubmit} className="px-5 py-5 flex flex-col gap-5">

                  <div>
                    <FieldLabel htmlFor="issue-type">Issue Type</FieldLabel>
                    <SelectField
                      id="issue-type"
                      value={issueType}
                      onChange={setIssueType}
                      options={ISSUE_TYPES}
                      required
                    />
                  </div>

                  <div>
                    <FieldLabel htmlFor="priority">Priority</FieldLabel>
                    <SelectField
                      id="priority"
                      value={priority}
                      onChange={setPriority}
                      options={PRIORITIES}
                      required
                    />
                  </div>

                  <div>
                    <FieldLabel htmlFor="description">Description</FieldLabel>
                    <textarea
                      id="description"
                      rows={5}
                      required
                      placeholder="Describe the issue in detail. Include steps to reproduce if applicable…"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className={clsx(
                        "w-full bg-white border border-brand-border rounded-md",
                        "px-3 py-2 text-sm text-brand-charcoal resize-none",
                        "placeholder:text-brand-muted/60",
                        "focus:outline-none focus:ring-2 focus:ring-brand-yellow/40 focus:border-brand-yellow",
                        "transition-colors"
                      )}
                    />
                  </div>

                  <div className="flex items-start gap-2 bg-brand-cream border border-brand-border rounded-md px-3 py-2.5">
                    <AlertCircle size={13} className="text-brand-muted shrink-0 mt-0.5" />
                    <p className="text-[0.68rem] text-brand-muted leading-relaxed">
                      For urgent outages, contact the System Administrator directly via the directory
                      on the right. Average response time:{" "}
                      <span className="font-semibold text-brand-charcoal">1–2 business days</span>.
                    </p>
                  </div>

                  <div className="pt-1">
                    <button
                      type="submit"
                      disabled={submitting}
                      className="btn-primary flex items-center gap-2 w-full justify-center disabled:opacity-60"
                    >
                      {submitting ? (
                        <>
                          <svg
                            className="animate-spin h-4 w-4 shrink-0"
                            viewBox="0 0 24 24"
                            fill="none"
                          >
                            <circle className="opacity-25" cx="12" cy="12" r="10"
                              stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor"
                              d="M4 12a8 8 0 018-8v8H4z" />
                          </svg>
                          Submitting…
                        </>
                      ) : (
                        <>
                          <SendHorizonal size={14} />
                          Submit Ticket
                        </>
                      )}
                    </button>
                  </div>

                </form>
              )}

            </div>

            {/* ── RIGHT: PIC Contact Card ───────────────────────────────── */}
            <div className="bg-brand-panel border border-brand-border rounded-md overflow-hidden">

              <div className="px-5 pt-4 pb-3 border-b border-brand-border flex items-center gap-2.5">
                <Building2 size={14} className="text-brand-muted shrink-0" />
                <div>
                  <h2 className="text-sm font-bold text-brand-charcoal font-heading">
                    System Administrator / PIC
                  </h2>
                  <p className="text-[0.68rem] text-brand-muted mt-0.5">
                    Primary point of contact for SHIELD system queries.
                  </p>
                </div>
              </div>

              {/* Avatar + name block */}
              <div className="px-5 py-5 flex items-center gap-4 border-b border-brand-border">
                <div
                  className="h-14 w-14 rounded-md bg-brand-charcoal flex items-center justify-center shrink-0"
                  aria-hidden="true"
                >
                  <span className="font-mono font-bold text-xl text-brand-yellow">
                    {PIC.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
                  </span>
                </div>
                <div>
                  <p className="text-base font-bold text-brand-charcoal font-heading leading-tight">
                    {PIC.name}
                  </p>
                  <p className="text-xs text-brand-muted mt-0.5">{PIC.role}</p>
                </div>
              </div>

              {/* Contact rows */}
              <div className="divide-y divide-brand-border">
                <ContactRow icon={<User size={14} />} label="Full Name" value={PIC.name} />
                <ContactRow icon={<BadgeCheck size={14} />} label="Role / Title" value={PIC.role} />
                <ContactRow icon={<Phone size={14} />} label="Internal Extension" value={PIC.ext} mono />
                <ContactRow icon={<Mail size={14} />} label="Internal Email" value={PIC.email} mono />
              </div>

              {/* Availability */}
              <div className="px-5 py-4 border-t border-brand-border bg-brand-cream/60">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-sm bg-[#16A34A] shrink-0" aria-label="Available" />
                  <p className="text-[0.68rem] text-brand-muted">
                    Available{" "}
                    <span className="font-semibold text-brand-charcoal">Mon – Fri, 09:00 – 18:00 MYT</span>
                  </p>
                </div>
                <p className="text-[0.65rem] text-brand-muted/70 mt-1.5 leading-relaxed">
                  This is an internal JuneBank directory entry. Do not share outside the organisation.
                  For system emergencies outside business hours, escalate via the JuneBank NOC hotline.
                </p>
              </div>

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
