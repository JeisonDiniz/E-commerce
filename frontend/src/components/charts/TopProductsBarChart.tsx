import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TopProduct } from "../../types";
import { CATEGORICAL, CHROME } from "./palette";

// Série única -> uma cor (slot 1); rótulo direto no fim de cada barra (poucas barras, cabe bem).
export function TopProductsBarChart({ data }: { data: TopProduct[] }) {
  const chartData = [...data].reverse(); // maior valor no topo

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 36)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 32, left: 8, bottom: 0 }} barCategoryGap={8}>
        <CartesianGrid stroke={CHROME.gridline} horizontal={false} />
        <XAxis type="number" stroke={CHROME.baseline} tick={{ fill: CHROME.textMuted, fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="product_name"
          width={140}
          stroke={CHROME.baseline}
          tick={{ fill: CHROME.textSecondary, fontSize: 12 }}
        />
        <Tooltip
          formatter={(value) => [`${value} un.`, "Vendidos"]}
          contentStyle={{ borderRadius: 8, borderColor: CHROME.gridline, fontSize: 12 }}
        />
        <Bar dataKey="units_sold" fill={CATEGORICAL[0]} radius={[0, 4, 4, 0]} maxBarSize={20}>
          <LabelList dataKey="units_sold" position="right" style={{ fill: CHROME.textSecondary, fontSize: 12 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}