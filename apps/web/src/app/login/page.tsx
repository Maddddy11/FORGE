"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth, ROLES, type Role } from "@/lib/auth";

export default function LoginPage() {
  const { login, role, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && role) router.replace("/");
  }, [ready, role, router]);

  function handleLogin(r: Role) {
    login(r);
    router.push("/");
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "var(--bg)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem",
    }}>
      <div style={{ marginBottom: "2.5rem", textAlign: "center" }}>
        <div style={{
          fontFamily: "var(--font-mono)",
          fontSize: "1.5rem",
          fontWeight: 700,
          letterSpacing: ".2em",
          color: "var(--text-primary)",
          marginBottom: ".5rem",
        }}>
          FOR<span style={{ fontWeight: 300, opacity: .5 }}>GE</span>
        </div>
        <div style={{
          fontFamily: "var(--font-sans)",
          fontSize: ".875rem",
          color: "var(--text-helper)",
        }}>
          Industrial Maintenance Co-Pilot
        </div>
      </div>

      <div style={{
        background: "var(--layer-01)",
        border: "1px solid var(--border-subtle)",
        padding: "2rem",
        width: "100%",
        maxWidth: "480px",
      }}>
        <div style={{
          fontSize: ".6875rem",
          fontWeight: 700,
          letterSpacing: ".12em",
          textTransform: "uppercase",
          color: "var(--text-helper)",
          marginBottom: "1.25rem",
          paddingBottom: ".5rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}>
          Select Role — Demo Access
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: ".75rem" }}>
          {(Object.entries(ROLES) as [Role, typeof ROLES[Role]][]).map(([key, val]) => (
            <button
              key={key}
              onClick={() => handleLogin(key)}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                gap: ".25rem",
                padding: "1rem 1.25rem",
                background: "var(--bg)",
                border: "1px solid var(--border-subtle)",
                cursor: "pointer",
                textAlign: "left",
                transition: "border-color .12s, background .12s",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--interactive)";
                (e.currentTarget as HTMLButtonElement).style.background = "var(--layer-02)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-subtle)";
                (e.currentTarget as HTMLButtonElement).style.background = "var(--bg)";
              }}
            >
              <span style={{
                fontFamily: "var(--font-mono)",
                fontSize: ".8125rem",
                fontWeight: 700,
                letterSpacing: ".08em",
                textTransform: "uppercase",
                color: key === "admin" ? "var(--warning)"
                     : key === "approver" ? "var(--success)"
                     : "var(--text-primary)",
              }}>
                {val.label}
              </span>
              <span style={{
                fontFamily: "var(--font-sans)",
                fontSize: ".8125rem",
                color: "var(--text-helper)",
              }}>
                {val.description}
              </span>
            </button>
          ))}
        </div>

        <div style={{
          marginTop: "1.25rem",
          paddingTop: "1rem",
          borderTop: "1px solid var(--border-subtle)",
          fontSize: ".75rem",
          color: "var(--text-helper)",
          fontFamily: "var(--font-sans)",
        }}>
          Demo environment — no password required. Token is stored in your browser.
        </div>
      </div>
    </div>
  );
}
