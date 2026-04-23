import {
  createContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

export interface AuthContextValue {
  isAuthenticated: boolean;
  needsAuth: boolean;
  login: (token: string) => Promise<boolean>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue>({
  isAuthenticated: false,
  needsAuth: false,
  login: async () => false,
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem("aicmo_token"),
  );
  const [needsAuth, setNeedsAuth] = useState(false);

  // Listen for 401 events from apiFetch
  useEffect(() => {
    const handler = () => {
      setIsAuthenticated(false);
      setNeedsAuth(true);
      queryClient.cancelQueries();
    };
    window.addEventListener("aicmo:unauthorized", handler);
    return () => window.removeEventListener("aicmo:unauthorized", handler);
  }, [queryClient]);

  // On mount, probe to detect if auth is needed
  useEffect(() => {
    fetch("/api/v1/projects").then((r) => {
      if (r.status === 401) {
        setNeedsAuth(true);
        if (!localStorage.getItem("aicmo_token")) {
          setIsAuthenticated(false);
        }
      }
    });
  }, []);

  const login = useCallback(
    async (token: string) => {
      const resp = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      if (resp.ok) {
        localStorage.setItem("aicmo_token", token);
        setIsAuthenticated(true);
        queryClient.invalidateQueries();
        return true;
      }
      return false;
    },
    [queryClient],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("aicmo_token");
    setIsAuthenticated(false);
    queryClient.cancelQueries();
  }, [queryClient]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, needsAuth, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
