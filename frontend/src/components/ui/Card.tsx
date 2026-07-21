import type { PropsWithChildren } from "react";

export function Card({ children, className = "" }: PropsWithChildren<{ className?: string }>) {
  return (
    <div className={`rounded-2xl border border-[var(--border-hairline)] bg-[var(--surface-card)] p-5 ${className}`}>
      {children}
    </div>
  );
}