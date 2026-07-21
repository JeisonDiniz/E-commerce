type Status = "good" | "warning" | "serious" | "critical" | "neutral";

const STATUS_STYLES: Record<Status, { dot: string; text: string }> = {
  good: { dot: "bg-[var(--status-good)]", text: "text-green-800" },
  warning: { dot: "bg-[var(--status-warning)]", text: "text-amber-800" },
  serious: { dot: "bg-[var(--status-serious)]", text: "text-orange-800" },
  critical: { dot: "bg-[var(--status-critical)]", text: "text-red-800" },
  neutral: { dot: "bg-neutral-400", text: "text-neutral-700" },
};

interface BadgeProps {
  status: Status;
  label: string;
}

// Status nunca só por cor: sempre acompanhado de um rótulo textual (regra da skill de dataviz).
export function Badge({ status, label }: BadgeProps) {
  const style = STATUS_STYLES[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full bg-neutral-100 px-2.5 py-1 text-xs font-medium ${style.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {label}
    </span>
  );
}