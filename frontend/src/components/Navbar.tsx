"use client";

// =============================================================================
// JuneBank — Top Navigation Bar
// Fixed, cream background, Ubuntu font.
// Left: nav links with yellow underline hover animation.
// Right: JuneBank logo + Profile dropdown (Settings, Logout).
// =============================================================================

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import clsx from "clsx";
import { useAuth } from "@/lib/auth";

const NAV_LINKS = [
  { label: "Home", href: "/" },
  { label: "Logs", href: "/logs" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Contact", href: "/contact" },
];

// ---------------------------------------------------------------------------
// Profile Dropdown
// ---------------------------------------------------------------------------
function ProfileDropdown() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const initial = user?.username?.[0]?.toUpperCase() ?? "U";

  return (
    <div ref={ref} className="relative">

      {/* Trigger button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "flex items-center gap-2.5 px-3 py-1.5 rounded-lg border transition-colors duration-150",
          open
            ? "bg-brand-yellow/15 border-brand-yellow/40"
            : "bg-transparent border-brand-border hover:bg-brand-yellow/10 hover:border-brand-yellow/30"
        )}
        aria-haspopup="true"
        aria-expanded={open}
      >
        {/* Avatar circle */}
        <span className="h-7 w-7 rounded-full bg-brand-yellow flex items-center justify-center
                         text-brand-charcoal font-bold text-xs font-heading shrink-0">
          {initial}
        </span>

        {/* Username */}
        <span className="text-sm font-medium text-brand-charcoal font-heading hidden sm:block">
          {user?.username}
        </span>

        {/* Chevron */}
        <svg
          width="12" height="12" viewBox="0 0 12 12" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          className={clsx(
            "text-brand-muted transition-transform duration-200",
            open && "rotate-180"
          )}
        >
          <polyline points="2 4 6 8 10 4" />
        </svg>
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-52 bg-brand-panel border border-brand-border
                     rounded-xl shadow-card overflow-hidden animate-fade-in z-50"
        >
          {/* User info header */}
          <div className="px-4 py-3 border-b border-brand-border">
            <p className="text-xs text-brand-muted uppercase tracking-widest font-semibold">
              Signed in as
            </p>
            <p className="text-sm font-bold text-brand-charcoal font-heading truncate mt-0.5">
              {user?.username}
            </p>
          </div>

          {/* Menu items */}
          <div className="py-1.5">
            <DropdownItem
              icon={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06
                           a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09
                           A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83
                           l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09
                           A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83
                           l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09
                           a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83
                           l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09
                           a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
              }
              label="Settings"
              onClick={() => {
                setOpen(false);
                router.push("/settings");
              }}
            />

            <div className="mx-3 my-1 h-px bg-brand-border" />

            <DropdownItem
              icon={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
              }
              label="Logout"
              onClick={() => {
                setOpen(false);
                logout();
              }}
              danger
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reusable dropdown menu item
// ---------------------------------------------------------------------------
function DropdownItem({
  icon,
  label,
  onClick,
  danger = false,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors duration-150",
        danger
          ? "text-risk-high hover:bg-risk-highBg"
          : "text-brand-charcoal hover:bg-brand-yellow/10"
      )}
    >
      <span className={danger ? "text-risk-high" : "text-brand-muted"}>{icon}</span>
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Navbar
// ---------------------------------------------------------------------------
export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 bg-brand-cream shadow-navbar"
      style={{ backdropFilter: "blur(8px)" }}
    >
      <div className="max-w-screen-2xl mx-auto px-8 h-16 flex items-center justify-between">

        {/* ---- Left: Navigation Links ---- */}
        <ul className="flex items-center gap-10">
          {NAV_LINKS.map(({ label, href }) => {
            const isActive = pathname === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={clsx(
                    "font-heading font-medium text-[0.95rem] tracking-wide",
                    "relative pb-0.5 transition-colors duration-200",
                    "group",
                    isActive
                      ? "text-brand-charcoal font-bold"
                      : "text-brand-muted hover:text-brand-charcoal"
                  )}
                >
                  {label}
                  <span
                    className={clsx(
                      "absolute bottom-0 left-0 h-[2px] bg-brand-yellow rounded-full",
                      "transition-all duration-250 origin-left",
                      isActive ? "w-full" : "w-0 group-hover:w-full"
                    )}
                  />
                </Link>
              </li>
            );
          })}
        </ul>

        {/* ---- Right: JuneBank Logo + Profile ---- */}
        <div className="flex items-center gap-5">
          <ProfileDropdown />

          <div className="h-6 w-px bg-brand-border" />

          <Link href="/" className="flex items-center shrink-0">
            <Image
              src="/JuneBank.png"
              alt="JuneBank"
              width={148}
              height={40}
              priority
              style={{ objectFit: "contain" }}
            />
          </Link>
        </div>

      </div>
    </nav>
  );
}
