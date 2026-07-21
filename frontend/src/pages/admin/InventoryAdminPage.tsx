import { useEffect, useState } from "react";
import { fetchProducts } from "../../api/catalog";
import { createMovement, fetchLowStock } from "../../api/inventory";
import type { LowStockItem, MovementType, Product } from "../../types";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Spinner } from "../../components/ui/Spinner";

const MOVEMENT_OPTIONS: { value: MovementType; label: string }[] = [
  { value: "entrada", label: "Entrada (recebimento/reposição)" },
  { value: "saida", label: "Saída (venda manual/perda)" },
  { value: "ajuste", label: "Ajuste (inventário físico)" },
  { value: "devolucao", label: "Devolução" },
];

export function InventoryAdminPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [lowStock, setLowStock] = useState<LowStockItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ variant_id: "", movement_type: "entrada" as MovementType, quantity: 1, reason: "" });
  const [feedback, setFeedback] = useState<string | null>(null);

  function load() {
    setLoading(true);
    Promise.all([fetchProducts({ limit: 100 }), fetchLowStock()])
      .then(([prods, low]) => {
        setProducts(prods);
        setLowStock(low);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const variantOptions = products.flatMap((p) =>
    p.variants.map((v) => ({
      id: v.id,
      label: `${p.name} — ${v.size}/${v.color} (SKU ${v.sku}, estoque: ${v.stock_quantity ?? 0})`,
    }))
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.variant_id) {
      setFeedback("Selecione uma variante.");
      return;
    }
    await createMovement(form);
    setFeedback("Movimentação registrada com sucesso.");
    setForm({ ...form, quantity: 1, reason: "" });
    load();
  }

  if (loading) return <Spinner />;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Estoque</h1>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-sm font-semibold">Registrar movimentação</h2>
          <form onSubmit={handleSubmit} className="mt-3 space-y-3">
            <select
              value={form.variant_id}
              onChange={(e) => setForm({ ...form, variant_id: e.target.value })}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            >
              <option value="">Selecione a variante</option>
              {variantOptions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.label}
                </option>
              ))}
            </select>
            <select
              value={form.movement_type}
              onChange={(e) => setForm({ ...form, movement_type: e.target.value as MovementType })}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            >
              {MOVEMENT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={1}
              value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            />
            <input
              placeholder="Motivo (opcional)"
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            />
            <Button type="submit" className="w-full">
              Registrar
            </Button>
            {feedback && <p className="text-sm text-[var(--text-secondary)]">{feedback}</p>}
          </form>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold">Itens em risco de ruptura</h2>
          {lowStock.length === 0 ? (
            <EmptyState title="Nenhum item abaixo do estoque mínimo" />
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {lowStock.map((item) => (
                <li key={item.variant_id} className="flex items-center justify-between border-b border-[var(--border-hairline)] py-2 last:border-0">
                  <span>
                    {item.product_name} <span className="text-xs text-[var(--text-muted)]">({item.sku})</span>
                  </span>
                  <Badge status={item.quantity === 0 ? "critical" : "warning"} label={`${item.quantity} un.`} />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}