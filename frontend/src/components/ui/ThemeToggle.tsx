import { useTheme } from "../../hooks/useTheme";
import { IconMoon, IconSun } from "./icons";

/** Botão de alternância de tema claro/escuro — ver src/hooks/useTheme.ts. */
export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggleTheme}
      title={isDark ? "Mudar para tema claro" : "Mudar para tema escuro"}
      aria-label={isDark ? "Mudar para tema claro" : "Mudar para tema escuro"}
      className={`flex h-10 w-10 items-center justify-center rounded-full border border-[var(--border-hairline)] text-[var(--text-primary)] transition-colors hover:bg-[var(--accent-soft)] ${className}`}
    >
      {isDark ? <IconSun /> : <IconMoon />}
    </button>
  );
}
