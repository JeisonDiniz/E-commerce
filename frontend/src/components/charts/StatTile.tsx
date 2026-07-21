import { Card } from "../ui/Card";

interface StatTileProps {
  label: string;
  value: string;
  status?: "good" | "warning" | "critical";
}

const STATUS_RING: Record<string, string> = {
  good: "",
  warning: "ring-1 ring-[var(--status-warning)]",
  critical: "ring-1 ring-[var(--status-critical)]",
};

// Stat tile: label (sentence case, sem dois-pontos) + valor em destaque.
export function StatTile({ label, value, status }: StatTileProps) {
  return (
    <Card className={status ? STATUS_RING[status] : ""}>
      <p className="text-xs font-medium text-[var(--text-secondary)]">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">{value}</p>
    </Card>
  );
}