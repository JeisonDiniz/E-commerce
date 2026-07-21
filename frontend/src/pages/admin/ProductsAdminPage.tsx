import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { fetchCategories, fetchProducts } from "../../api/catalog";
import type { Category, GenderType, Product, SeasonType, SizeType } from "../../types";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Spinner } from "../../components/ui/Spinner";

const GENDERS: GenderType[] = ["unissex", "masculino", "feminino", "infantil"];
const SEASONS: SeasonType[] = ["o_ano_todo", "verao", "inverno", "outono", "primavera"];
const SIZES: SizeType[] = ["PP", "P", "M", "G", "GG", "XG"];

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function ProductsAdminPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const [form, setForm] = useState({
    category_id: "",
    name: "",
    brand: "",
    gender: "unissex" as GenderType,
    season: "o_ano_todo" as SeasonType,
    base_price: "",
    sku: "",
    size: "M" as SizeType,
    color: "",
  });

  function load() {
    setLoading(true);
    Promise.all([fetchProducts({ limit: 100 }), fetchCategories()])
      .then(([prods, cats]) => {
        setProducts(prods);
        setCategories(cats);
        if (cats.length > 0) setForm((f) => ({ ...f, category_id: f.category_id || cats[0].id }));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/products", {
        category_id: form.category_id,
        name: form.name,
        brand: form.brand,
        gender: form.gender,
        season: form.season,
        base_price: Number(form.base_price),
        variants: [{ sku: form.sku, size: form.size, color: form.color, price: Number(form.base_price) }],
      });
      setFeedback("Produto criado com sucesso.");
      setShowForm(false);
      load();
    } catch {
      setFeedback("Erro ao criar produto. Verifique se o SKU já existe.");
    }
  }

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Produtos</h1>
        <Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Cancelar" : "Novo produto"}</Button>
      </div>

      {feedback && <p className="mt-3 text-sm text-[var(--text-secondary)]">{feedback}</p>}

      {showForm && (
        <Card className="mt-4">
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-3">
            <select
              className="col-span-2 rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <input
              className="col-span-2 rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              placeholder="Nome do produto"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              placeholder="Marca"
              value={form.brand}
              onChange={(e) => setForm({ ...form, brand: e.target.value })}
            />
            <input
              type="number"
              step="0.01"
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              placeholder="Preço base"
              required
              value={form.base_price}
              onChange={(e) => setForm({ ...form, base_price: e.target.value })}
            />
            <select
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              value={form.gender}
              onChange={(e) => setForm({ ...form, gender: e.target.value as GenderType })}
            >
              {GENDERS.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
            <select
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              value={form.season}
              onChange={(e) => setForm({ ...form, season: e.target.value as SeasonType })}
            >
              {SEASONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <p className="col-span-2 mt-2 text-xs font-medium text-[var(--text-muted)]">Primeira variante</p>
            <input
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              placeholder="SKU"
              required
              value={form.sku}
              onChange={(e) => setForm({ ...form, sku: e.target.value })}
            />
            <input
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              placeholder="Cor"
              required
              value={form.color}
              onChange={(e) => setForm({ ...form, color: e.target.value })}
            />
            <select
              className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              value={form.size}
              onChange={(e) => setForm({ ...form, size: e.target.value as SizeType })}
            >
              {SIZES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <Button type="submit" className="col-span-2">
              Criar produto
            </Button>
          </form>
        </Card>
      )}

      <div className="mt-4 space-y-2">
        {products.map((p) => (
          <Card key={p.id} className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{p.name}</p>
              <p className="text-xs text-[var(--text-muted)]">
                {p.brand} · {p.gender} · {p.season} · {p.variants.length} variante(s)
              </p>
            </div>
            <p className="text-sm font-semibold">{formatCurrency(p.base_price)}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}