import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "@/styles/tokens.css";
import "@/styles/design-system.css";
import Layout from "@/components/layout/Layout";
import { ThemeProvider } from "@/components/ThemeProvider";
import Background from "@/components/Background";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PharmaAgent AI — Autonomous Pharmacy Assistant",
  description:
    "AI-powered pharmacy assistant. Order medicines, check prescriptions, and manage inventory with the power of Gemini AI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          {/* Fixed animated background — behind everything at z-index: 0 */}
          <Background />

          {/* All page content sits above the background */}
          <div style={{ position: "relative", zIndex: 1 }}>
            <Layout>{children}</Layout>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
