import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SHIELD | SME Risk Evaluator — JuneBank",
  description:
    "SME Health Indicator and Evaluator for Loan Decision. Powered by XGBoost + SHAP explainability.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-brand-bg antialiased">{children}</body>
    </html>
  );
}
