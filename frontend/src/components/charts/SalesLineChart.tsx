import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailySalesPoint } from "../../types";
import { CHROME, SEQUENTIAL_BLUE } from "./palette";
import { formatCurrency } from "../../utils/currency";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

// Série única (faturamento diário) -> sem legenda (o título do card já identifica a série).
export function SalesLineChart({ data }: { data: DailySalesPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <defs>
          <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={SEQUENTIAL_BLUE} stopOpacity={0.1} />
            <stop offset="100%" stopColor={SEQUENTIAL_BLUE} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={CHROME.gridline} vertical={false} />
        <XAxis
          dataKey="sale_date"
          tickFormatter={formatDate}
          stroke={CHROME.baseline}
          tick={{ fill: CHROME.textMuted, fontSize: 12 }}
          minTickGap={32}
        />
        <YAxis
          stroke={CHROME.baseline}
          tick={{ fill: CHROME.textMuted, fontSize: 12 }}
          tickFormatter={(v) => `R$${Math.round(v / 1000)}k`}
          width={48}
        />
        <Tooltip
          formatter={(value) => [formatCurrency(Number(value)), "Faturamento"]}
          labelFormatter={(label) => formatDate(label as string)}
          contentStyle={{ borderRadius: 8, borderColor: CHROME.gridline, fontSize: 12 }}
        />
        <Area
          type="monotone"
          dataKey="revenue"
          stroke={SEQUENTIAL_BLUE}
          strokeWidth={2}
          fill="url(#revenueFill)"
          dot={false}
          activeDot={{ r: 4, stroke: CHROME.surface, strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}