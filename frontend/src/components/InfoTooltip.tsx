"use client";

// =============================================================================
// SHIELD — InfoTooltip (shared)
//
// A small ? icon that shows a plain-English explanation popover on hover.
// Rendered via React portal onto document.body so it is NEVER clipped by
// any ancestor with overflow:hidden or a stacking context.
//
// Positioning logic:
//   • Prefers RIGHT of the icon.
//   • Falls back to LEFT when there is more space on that side.
//   • Vertically centres on the icon, clamped inside the viewport.
//   • Caret arrow flips direction to match.
//
// Usage:
//   <InfoTooltip text="This ratio measures …" />
// =============================================================================

import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { HelpCircle } from "lucide-react";

interface Props {
  text: string;
  /** Icon size in px. Default 12. */
  size?: number;
}

const CARD_W  = 260;
const CARD_GAP = 8;
const CARD_H_EST = 140; // rough height estimate for vertical clamping

export default function InfoTooltip({ text, size = 12 }: Props) {
  const [visible,    setVisible]    = useState(false);
  const [cardStyle,  setCardStyle]  = useState<React.CSSProperties>({});
  const [caretStyle, setCaretStyle] = useState<React.CSSProperties>({});
  const iconRef  = useRef<HTMLButtonElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const show = () => {
    if (timerRef.current) clearTimeout(timerRef.current);

    if (iconRef.current) {
      const r  = iconRef.current.getBoundingClientRect();
      const vw = window.innerWidth;
      const vh = window.innerHeight;

      const spaceRight = vw - r.right;
      const spaceLeft  = r.left;
      const placeRight = spaceRight >= CARD_W + CARD_GAP || spaceRight >= spaceLeft;

      const cardLeft = placeRight
        ? r.right + CARD_GAP
        : r.left - CARD_W - CARD_GAP;

      let cardTop = r.top + r.height / 2 - CARD_H_EST / 2;
      cardTop = Math.max(8, Math.min(cardTop, vh - CARD_H_EST - 8));

      // Caret vertical offset: align with icon centre relative to card top
      const caretTop = r.top + r.height / 2 - cardTop - 5;

      setCardStyle({
        position : "fixed",
        top      : cardTop,
        left     : cardLeft,
        width    : CARD_W,
        zIndex   : 9999,
      });

      setCaretStyle({
        position : "absolute",
        top      : caretTop,
        width    : 10,
        height   : 10,
        background   : "white",
        borderWidth  : 1,
        borderStyle  : "solid",
        borderColor  : "#E8E4DE",
        transform    : "rotate(45deg)",
        ...(placeRight
          ? { left: -5,  borderLeft: "none",  borderBottom: "none" }
          : { right: -5, borderRight: "none", borderTop: "none"    }),
      });
    }

    setVisible(true);
  };

  const hide     = () => { timerRef.current = setTimeout(() => setVisible(false), 150); };
  const keepOpen = () => { if (timerRef.current) clearTimeout(timerRef.current); };

  const popover =
    visible && mounted
      ? createPortal(
          <div
            role="tooltip"
            style={cardStyle}
            onMouseEnter={keepOpen}
            onMouseLeave={hide}
            className="bg-brand-panel border border-brand-border rounded-lg shadow-card px-3 py-2.5 animate-fade-in"
          >
            <span aria-hidden="true" style={caretStyle} />
            <p className="text-[0.68rem] leading-relaxed text-brand-subtext">{text}</p>
          </div>,
          document.body
        )
      : null;

  return (
    <>
      <button
        ref={iconRef}
        type="button"
        tabIndex={0}
        aria-label="More information"
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        className="text-brand-muted hover:text-brand-charcoal transition-colors
                   focus:outline-none focus-visible:ring-1 focus-visible:ring-brand-yellow/60
                   rounded shrink-0 inline-flex items-center"
      >
        <HelpCircle size={size} />
      </button>
      {popover}
    </>
  );
}
