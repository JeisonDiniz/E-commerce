import { useEffect, useState } from "react";
import { fetchInventoryStatus, fetchSalesSummary, fetchTopProducts } from "../../api/reports";
import { fetchCategories } from "../../api/catalog";
import { fetchCategoryPredictions } from "../../api/predictions";
import { fetchLowStock } from "../../api/inventory";
import type { Category, DailySalesPoint, InventoryStatusSummary, LowStockItem, MLPrediction, TopProduct } from "../../types";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { StatTile } from "../../components/charts/StatTile";
import { SalesLineChart } from "../../components/charts/SalesLineChart";
import { TopProductsBarChart } from "../../components/charts/TopProductsBarChart";
import { CategoryTrendChart } from "../../components/charts/CategoryTrendChart";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [sales, setSales] = useState<DailySalesPoint[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [inventoryStatus, setInventoryStatus] = useState<InventoryStatusSummary | null>(null);
  const [lowStock, setLowStock] = useState<LowStockItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [predictions, setPredictions] = useState<MLPrediction[]>([]);
  const [predictionsError, setPredictionsError] = useState(false);

  useEffect(() => {
    Promise.all([fetchSalesSummary(), fetchTopProducts(8), fetchInventoryStatus(), fetchLowStock(), fetchCategories()])
      .then(([salesData, top, status, low, cats]) => {
        setSales(salesData);
        setTopProducts(top);
        setInventoryStatus(status);
        setLowStock(low);
        setCategories(cats);
        if (cats.length > 0) setSelectedCategory(cats[0].id);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedCategory) return;
    setPredictionsError(false);
    fetchCategoryPredictions(selectedCategory)
      .then(setPredictions)
      .catch(() => setPredictionsError(true));
  }, [selectedCategory]);

  if (loading) return <Spinner label="Carregando dashboard..." />;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Dashboard gerencial</h1>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Variantes cadastradas" value={String(inventoryStatus?.total_variants ?? 0)} />
        <StatTile label="Unidades em estoque" value={(inventoryStatus?.total_units_in_stock ?? 0).toLocaleString("pt-BR")} />
        <StatTile
          label="Itens abaixo do mínimo"
          value={String(inventoryStatus?.variants_below_min ?? 0)}
          status={(inventoryStatus?.variants_below_min ?? 0) > 0 ? "warning" : "good"}
        />
        <StatTile label="Faturamento no período" value={formatCurrency(sales.reduce((s, p) => s + p.revenue, 0))} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-sm font-semibold">Vendas diárias (faturamento)</h2>
          <SalesLineChart data={sales} />
        </Card>
        <Card>
          <h2 className="text-sm font-semibold">Produtos mais vendidos</h2>
          <TopProductsBarChart data={topProducts} />
        </Card>
      </div>

      <Card className="mt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Tendência de demanda por categoria (Prophet)</h2>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-md border border-neutral-300 px-2 py-1 text-sm"
          >
            {categories
              .filter((c) => !c.parent_id)
              .map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
          </select>
        </div>
        {predictionsError || predictions.length === 0 ? (
          <EmptyState
            title="Nenhuma previsão disponível ainda"
            description="Rode `python -m app.ml.train --source db` no back-end para gerar as previsões desta categoria."
          />
        ) : (
          <CategoryTrendChart predictions={predictions} />
        )}
      </Card>

      <Card className="mt-4">
        <h2 className="text-sm font-semibold">Itens em risco de ruptura de estoque</h2>
        {lowStock.length === 0 ? (
          <EmptyState title="Nenhum item abaixo do estoque mínimo" />
        ) : (
          <table className="mt-3 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border-hairline)] text-xs text-[var(--text-muted)]">
                <th className="pb-2">SKU</th>
                <th className="pb-2">Produto</th>
                <th className="pb-2">Estoque</th>
                <th className="pb-2">Mínimo</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {lowStock.map((item) => (
                <tr key={item.variant_id} className="border-b border-[var(--border-hairline)] last:border-0">
                  <td className="py-2 text-xs text-[var(--text-muted)]">{item.sku}</td>
                  <td className="py-2">{item.product_name}</td>
                  <td className="py-2">{item.quantity}</td>
                  <td className="py-2">{item.min_quantity}</td>
                  <td className="py-2">
                    <Badge status={item.quantity === 0 ? "critical" : "warning"} label={item.quantity === 0 ? "Ruptura" : "Baixo"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}