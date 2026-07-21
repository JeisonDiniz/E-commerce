import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-[var(--ink)] text-white hover:bg-[var(--ink-soft)] disabled:bg-neutral-300",
  secondary: "bg-white text-[var(--ink)] border border-neutral-300 hover:border-[var(--ink)]",
  danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
  ghost: "bg-transparent text-neutral-700 hover:bg-neutral-100",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  );
}

// Botão circular só com ícone (usado no header: conta, favoritos, etc.).
export function IconButton({ className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--ink)] text-white transition-colors hover:bg-[var(--ink-soft)] ${className}`}
      {...props}
    />
  );
}