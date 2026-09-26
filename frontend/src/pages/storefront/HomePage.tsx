import { useEffect, useMemo, useState } from "react";
import { fetchCategories, fetchProducts } from "../../api/catalog";
import type { Category, Product } from "../../types";
import { ProductCard } from "../../components/product/ProductCard";
import { Spinner } from "../../components/ui/Spinner";
import { EmptyState } from "../../components/ui/EmptyState";
import { Button } from "../../components/ui/Button";
import { IconArrowRight, IconHanger, IconSearch } from "../../components/ui/icons";

const SIZES = ["PP", "P", "M", "G", "GG", "XG"];

export function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const [categoryId, setCategoryId] = useState("");
  const [search, setSearch] = useState("");
  const [size, setSize] = useState("");
  const [onlyInStock, setOnlyInStock] = useState(false);
  const [maxPrice, setMaxPrice] = useState("");

  useEffect(() => {
    fetchCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchProducts({ category_id: categoryId || undefined })
      .then(setProducts)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [categoryId]);

  const topCategories = categories.filter((c) => !c.parent_id);

  const filtered = useMemo(() => {
    return products.filter((p) => {
      if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
      if (size && !p.variants.some((v) => v.size === size)) return false;
      if (maxPrice && p.base_price > Number(maxPrice)) return false;
      if (onlyInStock) {
        const stock = p.variants.reduce((sum, v) => sum + (v.stock_quantity ?? 0), 0);
        if (stock <= 0) return false;
      }
      return true;
    });
  }, [products, search, size, maxPrice, onlyInStock]);

  return (
    <div className="mx-auto max-w-[1400px]">
      {/* Hero */}
      <section className="grid gap-8 pb-14 lg:grid-cols-[280px_1fr]">
        <div className="flex flex-col justify-between">
          <ul className="space-y-1 text-sm tracked text-[var(--text-secondary)]">
            {topCategories.slice(0, 3).map((c) => (
              <li key={c.id}>
                <button onClick={() => setCategoryId(c.id)} className="uppercase hover:text-[var(--ink)]">
                  {c.name}
                </button>
              </li>
            ))}
          </ul>

          <div className="mt-10 lg:mt-0">
            <h1 className="font-display text-5xl sm:text-6xl">
              NOVA
              <br />
              COLEÇÃO
            </h1>
            <p className="mt-4 text-sm text-[var(--text-secondary)]">Temporada 2026</p>
            <a href="#catalogo">
              <Button className="mt-6 pl-6">
                Ver catálogo
                <IconArrowRight width={16} height={16} />
              </Button>
            </a>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Placeholder editorial pra quando ainda não há campanha fotográfica
              pronta: blocos de cor sólida com o ícone de cabide como marca
              d'água discreta, não uma ilustração literal — evita a cara de
              "protótipo com emoji" enquanto não tem foto de verdade. */}
          <div className="flex h-64 items-center justify-center rounded-2xl bg-[#e9e7e0] sm:h-80">
            <IconHanger width={72} height={72} className="text-[var(--ink)]/10" strokeWidth={1} />
          </div>
          <div className="mt-8 flex h-64 items-center justify-center rounded-2xl bg-[#dedcd2] sm:h-80">
            <IconHanger width={72} height={72} className="text-[var(--ink)]/10" strokeWidth={1} />
          </div>
        </div>
      </section>

      {/* Listagem */}
      <section id="catalogo" className="scroll-mt-24 border-t border-[var(--border-hairline)] pt-8">
        <p className="text-xs tracked text-[var(--text-muted)]">INÍCIO / PRODUTOS</p>
        <div className="mt-1 flex flex-wrap items-end justify-between gap-4">
          <h2 className="font-display text-3xl">PRODUTOS</h2>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <div className="flex h-11 flex-1 min-w-[200px] items-center gap-2 rounded-full bg-[#e9e7e0] px-4 text-sm text-[var(--text-muted)]">
            <IconSearch width={16} height={16} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar produtos"
              className="w-full bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setCategoryId("")}
              className={`rounded-full border px-4 py-2 text-xs tracked uppercase ${
                categoryId === "" ? "border-[var(--ink)] bg-[var(--ink)] text-white" : "border-[var(--border-strong)]"
              }`}
            >
              Todos
            </button>
            {topCategories.map((c) => (
              <button
                key={c.id}
                onClick={() => setCategoryId(c.id)}
                className={`rounded-full border px-4 py-2 text-xs tracked uppercase ${
                  categoryId === c.id ? "border-[var(--ink)] bg-[var(--ink)] text-white" : "border-[var(--border-strong)]"
                }`}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[220px_1fr]">
          <aside className="space-y-6">
            <div>
              <p className="text-sm font-semibold">Tamanho</p>
              <div className="mt-2 grid grid-cols-3 gap-1.5">
                {SIZES.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSize(size === s ? "" : s)}
                    className={`rounded-lg border py-1.5 text-xs ${
                      size === s ? "border-[var(--ink)] bg-[var(--ink)] text-white" : "border-[var(--border-strong)]"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-sm font-semibold">Disponibilidade</p>
              <label className="mt-2 flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <input type="checkbox" checked={onlyInStock} onChange={(e) => setOnlyInStock(e.target.checked)} />
                Somente em estoque
              </label>
            </div>

            <div>
              <p className="text-sm font-semibold">Preço máximo</p>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="R$"
                className="mt-2 w-full rounded-lg border border-[var(--border-strong)] px-3 py-1.5 text-sm"
              />
            </div>
          </aside>

          <div>
            {loading ? (
              <Spinner />
            ) : filtered.length === 0 ? (
              <EmptyState title="Nenhum produto encontrado" description="Tente ajustar os filtros." />
            ) : (
              <div className="grid grid-cols-2 gap-x-5 gap-y-8 sm:grid-cols-3 xl:grid-cols-4">
                {filtered.map((p) => (
                  <ProductCard key={p.id} product={p} />
                ))}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}