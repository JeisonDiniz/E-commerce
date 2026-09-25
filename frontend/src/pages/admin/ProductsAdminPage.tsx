import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { deleteProductImage, fetchCategories, fetchProducts, uploadProductImage } from "../../api/catalog";
import type { Category, GenderType, Product, SeasonType, SizeType } from "../../types";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Spinner } from "../../components/ui/Spinner";
import { colorToHex } from "../../utils/colors";
import { formatCurrency } from "../../utils/currency";

const MAX_IMAGE_MB = 5;
const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

function ProductImageManager({ product, onChanged }: { product: Product; onChanged: () => void }) {
  const variantColors = [...new Set(product.variants.map((v) => v.color))];
  const [color, setColor] = useState<string>(variantColors[0] ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setError(null);
    if (selected && !ACCEPTED_IMAGE_TYPES.includes(selected.type)) {
      setError("Formato não suportado. Use JPG, PNG ou WEBP.");
      setFile(null);
      setPreview(null);
      return;
    }
    if (selected && selected.size > MAX_IMAGE_MB * 1024 * 1024) {
      setError(`Imagem maior que ${MAX_IMAGE_MB}MB.`);
      setFile(null);
      setPreview(null);
      return;
    }
    setFile(selected);
    setPreview(selected ? URL.createObjectURL(selected) : null);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadProductImage(product.id, file, color || null);
      setFile(null);
      setPreview(null);
      onChanged();
    } catch {
      setError("Erro ao enviar imagem. Tente novamente.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(imageId: string) {
    await deleteProductImage(product.id, imageId);
    onChanged();
  }

  const imagesByColor = new Map<string, typeof product.images>();
  for (const img of product.images) {
    const key = img.color ?? "Geral";
    imagesByColor.set(key, [...(imagesByColor.get(key) ?? []), img]);
  }

  return (
    <div className="mt-3 border-t border-[var(--border-hairline)] pt-3">
      <p className="text-xs font-medium text-[var(--text-muted)]">Fotos por cor</p>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <select
          className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
          value={color}
          onChange={(e) => setColor(e.target.value)}
        >
          <option value="">Geral (sem cor específica)</option>
          {variantColors.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <input
          type="file"
          accept={ACCEPTED_IMAGE_TYPES.join(",")}
          onChange={handleFileChange}
          className="text-xs"
        />
        {preview && <img src={preview} alt="Pré-visualização" className="h-12 w-12 rounded-lg object-cover" />}
        <Button type="button" onClick={handleUpload} disabled={!file || uploading} className="px-4 py-2 text-xs">
          {uploading ? "Enviando..." : "Enviar imagem"}
        </Button>
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}

      {imagesByColor.size > 0 && (
        <div className="mt-3 space-y-2">
          {[...imagesByColor.entries()].map(([label, images]) => (
            <div key={label} className="flex items-center gap-2">
              <span
                className="h-3 w-3 shrink-0 rounded-full ring-1 ring-black/10"
                style={{ backgroundColor: label === "Geral" ? "#d4d4d4" : colorToHex(label) }}
                title={label}
              />
              <span className="w-24 shrink-0 text-xs text-[var(--text-muted)]">{label}</span>
              <div className="flex flex-wrap gap-2">
                {images.map((img) => (
                  <div key={img.id} className="group relative h-14 w-14 shrink-0 overflow-hidden rounded-lg">
                    <img src={img.url} alt={img.alt_text ?? product.name} className="h-full w-full object-cover" />
                    <button
                      type="button"
                      onClick={() => handleDelete(img.id)}
                      title="Remover imagem"
                      className="absolute inset-0 flex items-center justify-center bg-black/50 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100"
                    >
                      Remover
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const GENDERS: GenderType[] = ["unissex", "masculino", "feminino", "infantil"];
const SEASONS: SeasonType[] = ["o_ano_todo", "verao", "inverno", "outono", "primavera"];
const SIZES: SizeType[] = ["PP", "P", "M", "G", "GG", "XG"];

export function ProductsAdminPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [expandedProductId, setExpandedProductId] = useState<string | null>(null);

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

  // Reconsulta só a lista de produtos, sem acionar o spinner de página
  // inteira — usado depois de subir/remover uma imagem para não fechar o
  // painel de fotos que o usuário acabou de abrir.
  function refreshProducts() {
    fetchProducts({ limit: 100 }).then(setProducts).catch(console.error);
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
          <Card key={p.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium">{p.name}</p>
                <p className="text-xs text-[var(--text-muted)]">
                  {p.brand} · {p.gender} · {p.season} · {p.variants.length} variante(s) · {p.images.length} foto(s)
                </p>
              </div>
              <div className="flex items-center gap-3">
                <p className="text-sm font-semibold">{formatCurrency(p.base_price)}</p>
                <Button
                  type="button"
                  variant="secondary"
                  className="px-3 py-1.5 text-xs"
                  onClick={() => setExpandedProductId((cur) => (cur === p.id ? null : p.id))}
                >
                  {expandedProductId === p.id ? "Fechar fotos" : "Gerenciar fotos"}
                </Button>
              </div>
            </div>
            {expandedProductId === p.id && <ProductImageManager product={p} onChanged={refreshProducts} />}
          </Card>
        ))}
      </div>
    </div>
  );
}