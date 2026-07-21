import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchProduct } from "../../api/catalog";
import type { Product } from "../../types";
import { Spinner } from "../../components/ui/Spinner";
import { Button } from "../../components/ui/Button";
import { useAuthStore } from "../../store/authStore";
import { useCartStore } from "../../store/cartStore";
import { colorToHex } from "../../utils/colors";

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }).replace("R$", "$");
}

export function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { addItem } = useCartStore();

  const [product, setProduct] = useState<Product | null>(null);
  const [selectedSize, setSelectedSize] = useState<string>("");
  const [selectedColor, setSelectedColor] = useState<string>("");
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (productId) fetchProduct(productId).then(setProduct).catch(console.error);
  }, [productId]);

  const sizes = useMemo(() => [...new Set(product?.variants.map((v) => v.size) ?? [])], [product]);
  const colors = useMemo(() => [...new Set(product?.variants.map((v) => v.color) ?? [])], [product]);

  const selectedVariant = useMemo(
    () => product?.variants.find((v) => v.size === selectedSize && v.color === selectedColor),
    [product, selectedSize, selectedColor]
  );

  if (!product) return <Spinner />;

  async function handleAddToCart() {
    if (!user) {
      navigate("/login");
      return;
    }
    if (!selectedVariant) {
      setFeedback("Selecione tamanho e cor.");
      return;
    }
    await addItem(selectedVariant.id, 1);
    setFeedback("Adicionado à sacola!");
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-10 md:grid-cols-[80px_1fr_380px]">
      {/* Miniaturas */}
      <div className="order-2 flex gap-3 md:order-1 md:flex-col">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex aspect-square w-16 shrink-0 items-center justify-center rounded-lg bg-[#e9e7e0] text-xl md:w-full">
            👕
          </div>
        ))}
      </div>

      {/* Imagem principal */}
      <div className="order-1 flex aspect-square items-center justify-center rounded-2xl bg-[#e9e7e0] text-8xl md:order-2">
        👕
      </div>

      {/* Info */}
      <div className="order-3 rounded-2xl border border-[var(--border-hairline)] p-6">
        <p className="text-xs tracked uppercase text-[var(--text-muted)]">{product.brand}</p>
        <h1 className="mt-1 font-display text-2xl">{product.name}</h1>
        <p className="mt-2 text-xl font-semibold">{formatCurrency(product.base_price)}</p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">Preço à vista, sem parcelamento adicional</p>

        <p className="mt-4 text-sm text-[var(--text-secondary)]">{product.description}</p>

        <div className="mt-6">
          <p className="mb-2 text-sm font-medium">Cor</p>
          <div className="flex flex-wrap gap-2">
            {colors.map((color) => (
              <button
                key={color}
                onClick={() => setSelectedColor(color)}
                title={color}
                className={`h-8 w-8 rounded-full ring-1 ring-black/10 ${
                  selectedColor === color ? "outline outline-2 outline-offset-2 outline-[var(--ink)]" : ""
                }`}
                style={{ backgroundColor: colorToHex(color) }}
              />
            ))}
          </div>
        </div>

        <div className="mt-5">
          <p className="mb-2 text-sm font-medium">Tamanho</p>
          <div className="flex flex-wrap gap-2">
            {sizes.map((size) => (
              <button
                key={size}
                onClick={() => setSelectedSize(size)}
                className={`h-9 min-w-9 rounded-lg border px-2 text-sm ${
                  selectedSize === size ? "border-[var(--ink)] bg-[var(--ink)] text-white" : "border-[var(--border-strong)]"
                }`}
              >
                {size}
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs tracked uppercase text-[var(--text-muted)]">Encontre seu tamanho | Guia de medidas</p>
        </div>

        {selectedVariant && (
          <p className="mt-4 text-xs text-[var(--text-muted)]">
            SKU {selectedVariant.sku} · {selectedVariant.stock_quantity ?? 0} em estoque
          </p>
        )}

        <Button className="mt-6 w-full" onClick={handleAddToCart} disabled={selectedVariant?.stock_quantity === 0}>
          Adicionar
        </Button>

        {feedback && <p className="mt-2 text-sm text-[var(--text-secondary)]">{feedback}</p>}
      </div>
    </div>
  );
}