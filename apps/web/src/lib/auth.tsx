"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export const ROLES = {
  operator: {
    token: "imam-demo-operator",
    label: "Operator",
    description: "Submit incidents, view recommendations",
  },
  approver: {
    token: "imam-demo-approver",
    label: "Approver",
    description: "All operator access + approve / reject",
  },
  admin: {
    token: "imam-demo-admin",
    label: "Admin",
    description: "Full system access",
  },
} as const;

export type Role = keyof typeof ROLES;

interface AuthState {
  role: Role | null;
  token: string | null;
  ready: boolean;
  login: (role: Role) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  role: null, token: null, ready: false,
  login: () => {}, logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole]   = useState<Role | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("forge_role") as Role | null;
    if (stored && ROLES[stored]) {
      setRole(stored);
      setToken(ROLES[stored].token);
    }
    setReady(true);
  }, []);

  function login(r: Role) {
    localStorage.setItem("forge_role", r);
    setRole(r);
    setToken(ROLES[r].token);
  }

  function logout() {
    localStorage.removeItem("forge_role");
    setRole(null);
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ role, token, ready, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function canApprove(role: Role | null) {
  return role === "approver" || role === "admin";
}
