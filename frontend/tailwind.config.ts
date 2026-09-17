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
        // JuneBank brand palette — light/cream theme
        brand: {
          yellow:      "#FFD100",
          yellowHover: "#E6BC00",
          cream:       "#FCFAF8",       // main page background
          panel:       "#FFFFFF",       // card / panel background
          border:      "#E8E4DE",       // subtle warm border
          charcoal:    "#1A1A1A",       // primary text
          muted:       "#6B6B6B",       // secondary text
          subtext:     "#9A9A9A",       // tertiary / captions
        },
        risk: {
          low:          "#16A34A",
          lowBg:        "rgba(22,163,74,0.08)",
          moderate:     "#CA8A04",
          moderateBg:   "rgba(202,138,4,0.08)",
          high:         "#EA580C",
          highBg:       "rgba(234,88,12,0.08)",
          critical:     "#DC2626",
          criticalBg:   "rgba(220,38,38,0.08)",
          amber:        "#D97706",
        },
      },
      fontFamily: {
        // Ubuntu — headers, nav, wordmarks
        heading: ["Ubuntu", "system-ui", "sans-serif"],
        // Lato — body text, data, labels
        sans:    ["Lato", "system-ui", "sans-serif"],
        mono:    ["JetBrains Mono", "Courier New", "monospace"],
      },
      backgroundImage: {
        "navbar-gradient":
          "linear-gradient(180deg, #FCFAF8 0%, rgba(252,250,248,0.96) 100%)",
      },
      boxShadow: {
        navbar: "0 1px 0 0 #E8E4DE",
        panel:  "0 1px 4px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04)",
        card:   "0 2px 8px rgba(0,0,0,0.08)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        "gauge-fill": {
          from: { "stroke-dashoffset": "251" },
          to:   {},
        },
        "nav-underline": {
          from: { transform: "scaleX(0)" },
          to:   { transform: "scaleX(1)" },
        },
      },
      animation: {
        "fade-in":    "fade-in 0.3s ease-out both",
        "gauge-fill": "gauge-fill 1s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
