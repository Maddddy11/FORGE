"use client";

import Link from "next/link";
import { useAuth, ROLES } from "@/lib/auth";

export default function HeaderClient() {
  const { role, logout } = useAuth();

  return (
    <div style={{ display: "flex", alignItems: "center", marginLeft: "auto", gap: "1rem" }}>
      {role && (
        <>
          <span style={{
            fontSize: ".6875rem",
            fontWeight: 600,
            letterSpacing: ".1em",
            textTransform: "uppercase",
            color: "rgba(245,244,240,.45)",
            display: "flex",
            alignItems: "center",
            gap: ".5rem",
          }}>
            <span style={{
              padding: ".125rem .5rem",
              border: "1px solid rgba(245,244,240,.25)",
              color: role === "admin" ? "#fbbf24"
                   : role === "approver" ? "#86efac"
                   : "rgba(245,244,240,.65)",
            }}>
              {ROLES[role].label}
            </span>
          </span>
          <button
            onClick={logout}
            style={{
              background: "transparent",
              border: "1px solid rgba(245,244,240,.2)",
              color: "rgba(245,244,240,.45)",
              fontSize: ".6875rem",
              fontFamily: "var(--font-mono)",
              fontWeight: 600,
              letterSpacing: ".08em",
              textTransform: "uppercase",
              padding: ".25rem .625rem",
              cursor: "pointer",
            }}
          >
            Sign Out
          </button>
        </>
      )}
      {!role && (
        <Link
          href="/login"
          style={{
            fontSize: ".6875rem",
            fontWeight: 600,
            letterSpacing: ".1em",
            textTransform: "uppercase",
            color: "rgba(245,244,240,.5)",
            border: "1px solid rgba(245,244,240,.2)",
            padding: ".25rem .625rem",
            textDecoration: "none",
          }}
        >
          Sign In
        </Link>
      )}
      <span style={{
        display: "flex",
        alignItems: "center",
        gap: ".375rem",
        fontSize: ".6875rem",
        color: "rgba(245,244,240,.35)",
        letterSpacing: ".1em",
      }}>
        <span style={{
          width: 7, height: 7, borderRadius: "50%",
          background: "#22c55e", flexShrink: 0,
        }} />
        ONLINE
      </span>
    </div>
  );
}
