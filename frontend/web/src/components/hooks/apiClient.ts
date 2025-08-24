"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { createDefaultApi } from "@/lib/apiClient";
import type { DefaultApi } from "@jacantwell/kairos-api-client-ts";

const ApiContext = createContext<DefaultApi | null>(null);

// ----- PROVIDER -----
export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | undefined>(undefined);

  useEffect(() => {
    const t = localStorage.getItem("auth_token") ?? undefined;
    setToken(t);

    const handleStorage = () => {
      const updated = localStorage.getItem("auth_token") ?? undefined;
      setToken(updated);
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const api = useMemo(() => createDefaultApi(token), [token]);

  return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>;
}

// ----- HOOK -----
export function useApi() {
  const api = useContext(ApiContext);
  if (!api) throw new Error("useApi must be used within ApiProvider");
  return api;
}
