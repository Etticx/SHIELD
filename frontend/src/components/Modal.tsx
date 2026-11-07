"use client";

import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

interface ModalProps {
  title: string;
  subtitle?: string;
  onClose: () => void;
  /** Backdrop click closes only when true; use false while a form holds typed input. */
  dismissOnBackdrop?: boolean;
  children: ReactNode;
}

export default function Modal({ title, subtitle, onClose, dismissOnBackdrop = true, children }: ModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.45)", backdropFilter: "blur(4px)" }}
      onClick={dismissOnBackdrop ? onClose : undefined}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="bg-brand-panel rounded-2xl shadow-card border border-brand-border
                   w-full max-w-md animate-fade-in overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="h-1 w-full bg-brand-yellow" />
        <div className="px-7 py-6 flex flex-col gap-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-brand-charcoal font-heading">{title}</h2>
              {subtitle && <p className="text-sm text-brand-muted mt-0.5">{subtitle}</p>}
            </div>
            <button
              onClick={onClose}
              className="text-brand-muted hover:text-brand-charcoal transition-colors mt-0.5 p-1 rounded"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </div>
          <div className="h-px bg-brand-border" />
          {children}
        </div>
      </div>
    </div>
  );
}
