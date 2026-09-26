import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "theme";

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches;
}

function readStoredTheme(): Theme | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "dark" || stored === "light" ? stored : null;
  } catch {
    // localStorage indisponível (modo privado, storage bloqueado etc.) —
    // segue o tema do sistema sem persistir escolha.
    return null;
  }
}

function applyTheme(theme: Theme | null) {
  if (theme) {
    document.documentElement.setAttribute("data-theme", theme);
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

/**
 * Alternância de tema claro/escuro. Sem escolha manual salva, segue o tema
 * do sistema operacional (via @media prefers-color-scheme no CSS — ver
 * index.css); ao escolher manualmente, a preferência fica salva no
 * localStorage e passa a valer nesse navegador até ser trocada de novo.
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => readStoredTheme() ?? (systemPrefersDark() ? "dark" : "light"));

  useEffect(() => {
    applyTheme(readStoredTheme());
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((current) => {
      const next: Theme = current === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // segue funcionando na sessão atual, só não persiste entre visitas
      }
      return next;
    });
  }, []);

  return { theme, toggleTheme };
}
