import type { Metadata } from "next";
import Link from "next/link";
import { AuthProvider } from "@/lib/auth";
import HeaderClient from "@/components/HeaderClient";
import "./globals.css";

export const metadata: Metadata = {
  title: "Forge",
  description: "Industrial Maintenance Co-Pilot",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <div className="shell">
            <header className="header">
              <span className="header-brand">
                FOR<span>GE</span>
              </span>
              <nav>
                <ul className="header-nav">
                  <li><Link href="/">Dashboard</Link></li>
                  <li><Link href="/analyze">Analyze</Link></li>
                  <li><Link href="/approvals">Approvals</Link></li>
                </ul>
              </nav>
              <HeaderClient />
            </header>
            <main className="main">{children}</main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
