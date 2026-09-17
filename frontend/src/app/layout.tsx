import type { Metadata } from "next";
import { Ubuntu, Lato } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import AppShell from "@/components/AppShell";

// ---- Ubuntu — headings, navbar, wordmarks ----
const ubuntu = Ubuntu({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  variable: "--font-ubuntu",
  display: "swap",
});

// ---- Lato — body text, data labels, metrics ----
const lato = Lato({
  weight: ["400", "700"],
  subsets: ["latin"],
  variable: "--font-lato",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SHIELD | SME Risk Evaluator — JuneBank",
  description:
    "Early warning intelligence for better lending. JuneBank SHIELD evaluates SME credit risk using Random Forest + SHAP explainability.",
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png" },
    ],
    other: [
      { rel: "manifest", url: "/site.webmanifest" },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${ubuntu.variable} ${lato.variable}`}>
      <body className="min-h-screen bg-brand-cream font-sans antialiased text-brand-charcoal">
        {/*
          AuthProvider must wrap everything so SplashScreen, LoginPage,
          and Navbar can all read/write auth state.
          AppShell handles the splash → login → dashboard gate logic.
        */}
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
