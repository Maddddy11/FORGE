import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IMAM Lite Dashboard",
  description: "Incident analysis, approvals, and audit trail",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
