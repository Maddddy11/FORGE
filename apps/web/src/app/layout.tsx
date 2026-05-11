import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "IMAM Lite",
  description: "Institutional Memory & Asset Management Co-Pilot",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="header">
            <span className="header-brand">
              IMAM<span>LITE</span>
            </span>
            <nav>
              <ul className="header-nav">
                <li><Link href="/">Dashboard</Link></li>
                <li><Link href="/analyze">Analyze</Link></li>
                <li><Link href="/approvals">Approvals</Link></li>
              </ul>
            </nav>
            <div className="header-status">
              <span className="status-dot" />
              SYSTEM ONLINE
            </div>
          </header>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
