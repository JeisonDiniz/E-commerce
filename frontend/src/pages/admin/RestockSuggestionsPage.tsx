import { useEffect, useState } from "react";
import { fetchRestockSuggestions, reviewRestockSuggestion } from "../../api/predictions";
import type { RestockSuggestion } from "../../types";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Spinner } from "../../components/ui/Spinner";
import { EmptyState } from "../../components/ui/EmptyState";

const STATUS_BADGE = {
  pendente: { status: "warning" as const, label: "Pendente" },
  aprovada: { status: "good" as const, label: "Aprovada" },
  rejeitada: { status: "critical" as const, label: "Rejeitada" },
};

export function RestockSuggestionsPage() {
  const [suggestions, setSuggestions] = useState<RestockSuggestion[]>([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    fetchRestockSuggestions()
      .then(setSuggestions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleReview(id: string, approve: boolean) {
    await reviewRestockSuggestion(id, approve);
    load();
  }

  if (loading) return <Spinner />;

  const pending = suggestions.filter((s) => s.status === "pendente");
  const reviewed = suggestions.filter((s) => s.status !== "pendente");

  return (
    <div>
      <h1 className="text-2xl font-semibold">Sugestões de reposição</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Geradas pelo Random Forest a partir da demanda prevista para o próximo mês. A decisão de compra é sempre do
        gestor — nenhuma reposição é feita automaticamente.
      </p>

      <Card className="mt-6">
        <h2 className="text-sm font-semibold">Aguardando revisão ({pending.length})</h2>
        {pending.length === 0 ? (
          <EmptyState
            title="Nenhuma sugestão pendente"
            description="Rode `python -m app.ml.train --source db` no back-end para gerar novas sugestões."
          />
        ) : (
          <div className="mt-3 space-y-2">
            {pending.map((s) => (
              <div key={s.id} className="flex items-center justify-between rounded-md border border-[var(--border-hairline)] p-3">
                <div>
                  <p className="text-sm font-medium">Variante {s.variant_id.slice(0, 8)}</p>
                  <p className="text-xs text-[var(--text-muted)]">
                    Sugestão: repor {s.suggested_quantity} unidades
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => handleReview(s.id, false)}>
                    Rejeitar
                  </Button>
                  <Button onClick={() => handleReview(s.id, true)}>Aprovar</Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {reviewed.length > 0 && (
        <Card className="mt-4">
          <h2 className="text-sm font-semibold">Histórico de revisões</h2>
          <table className="mt-3 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border-hairline)] text-xs text-[var(--text-muted)]">
                <th className="pb-2">Variante</th>
                <th className="pb-2">Quantidade sugerida</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {reviewed.map((s) => (
                <tr key={s.id} className="border-b border-[var(--border-hairline)] last:border-0">
                  <td className="py-2 text-xs text-[var(--text-muted)]">{s.variant_id.slice(0, 8)}</td>
                  <td className="py-2">{s.suggested_quantity}</td>
                  <td className="py-2">
                    <Badge status={STATUS_BADGE[s.status].status} label={STATUS_BADGE[s.status].label} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}