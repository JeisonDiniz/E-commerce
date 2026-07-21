import { Link } from "react-router-dom";
import type { Product } from "../../types";
import { colorToHex } from "../../utils/colors";

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }).replace("R$", "$");
}

export function ProductCard({ product }: { product: Product }) {
  const totalStock = product.variants.reduce((sum, v) => sum + (v.stock_quantity ?? 0), 0);
  const colors = [...new Set(product.variants.map((v) => v.color))];

  return (
    <Link to={`/produtos/${product.id}`} className="group block">
      <div className="flex aspect-[4/5] items-center justify-center overflow-hidden rounded-2xl bg-[#e9e7e0] text-5xl transition-transform duration-200 group-hover:-translate-y-1">
        👕
      </div>

      <div className="mt-3 flex items-center gap-1.5">
        {colors.slice(0, 4).map((c) => (
          <span
            key={c}
            title={c}
            className="h-3.5 w-3.5 rounded-full ring-1 ring-black/10"
            style={{ backgroundColor: colorToHex(c) }}
          />
        ))}
        {colors.length > 4 && <span className="text-xs text-[var(--text-muted)]">+{colors.length - 4}</span>}
      </div>

      <div className="mt-1 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-[var(--text-primary)]">{product.name}</h3>
        <p className="shrink-0 text-sm font-semibold">{formatCurrency(product.base_price)}</p>
      </div>
      {totalStock === 0 && <p className="mt-0.5 text-xs font-medium text-red-600">Fora de estoque</p>}
    </Link>
  );
}