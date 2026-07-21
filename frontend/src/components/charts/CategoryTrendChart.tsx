import { Area, ComposedChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MLPrediction } from "../../types";
import { CHROME, SEQUENTIAL_BLUE } from "./palette";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

// Previsão do Prophet: linha (yhat) + faixa de confiança (yhat_lower..yhat_upper).
// Truque para a faixa "flutuante": uma área transparente até o limite inferior
// (empilhada) seguida de uma área visível cuja altura é (upper - lower).
export function CategoryTrendChart({ predictions }: { predictions: MLPrediction[] }) {
  const data = predictions.map((p) => ({
    date: p.prediction_date,
    yhat: p.predicted_quantity,
    lower: p.confidence_lower ?? p.predicted_quantity,
    band: (p.confidence_upper ?? p.predicted_quantity) - (p.confidence_lower ?? p.predicted_quantity),
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid stroke={CHROME.gridline} vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          stroke={CHROME.baseline}
          tick={{ fill: CHROME.textMuted, fontSize: 12 }}
          minTickGap={24}
        />
        <YAxis stroke={CHROME.baseline} tick={{ fill: CHROME.textMuted, fontSize: 12 }} width={40} />
        <Tooltip
          labelFormatter={(label) => formatDate(label as string)}
          formatter={(value, name) => [Math.round(Number(value) * 10) / 10, name === "yhat" ? "Previsão" : String(name)]}
          contentStyle={{ borderRadius: 8, borderColor: CHROME.gridline, fontSize: 12 }}
        />
        <Area type="monotone" dataKey="lower" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} />
        <Area
          type="monotone"
          dataKey="band"
          stackId="band"
          stroke="none"
          fill={SEQUENTIAL_BLUE}
          fillOpacity={0.12}
          isAnimationActive={false}
        />
        <Line type="monotone" dataKey="yhat" stroke={SEQUENTIAL_BLUE} strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}