import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // JuneBank brand palette
        brand: {
          yellow:  "#FFD100",
          yellowHover: "#E6BC00",
          bg:      "#0e1117",
          panel:   "#1a1c23",
          border:  "#2a2d36",
          muted:   "#6b7280",
          text:    "#f0f2f5",
          subtext: "#9ca3af",
        },
        risk: {
          high:    "#ef4444",
          highBg:  "rgba(239,68,68,0.12)",
          low:     "#22c55e",
          lowBg:   "rgba(34,197,94,0.12)",
          amber:   "#f59e0b",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "header-gradient":
          "linear-gradient(135deg, #12141c 0%, #0e1117 50%, #12141c 100%)",
      },
      boxShadow: {
        panel: "0 1px 3px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)",
        "yellow-glow": "0 0 20px rgba(255,209,0,0.25)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        "gauge-fill": {
          from: { "stroke-dashoffset": "251" },
          to:   {},
        },
      },
      animation: {
        "fade-in":   "fade-in 0.35s ease-out both",
        "gauge-fill": "gauge-fill 1s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
