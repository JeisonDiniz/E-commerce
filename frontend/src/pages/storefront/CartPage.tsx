import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCartStore } from "../../store/cartStore";
import { useAuthStore } from "../../store/authStore";
import { Button } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/EmptyState";
import { Spinner } from "../../components/ui/Spinner";
import { IconMinus, IconPlus, IconX } from "../../components/ui/icons";
import { formatCurrency } from "../../utils/currency";

export function CartPage() {
  const { cart, loading, refresh, updateItem, removeItem } = useCartStore();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"sacola" | "favoritos">("sacola");

  useEffect(() => {
    // O carrinho é por usuário autenticado (endpoint /cart exige login) — sem
    // isso, quem visita /carrinho deslogado gerava uma requisição fadada a
    // 401 (erro no console a cada carregamento da página, sem nenhum efeito
    // visível já que a tela trata cart=null como sacola vazia mesmo assim).
    if (user) refresh();
  }, [user, refresh]);

  if (user && loading && !cart) return <Spinner />;

  const items = cart?.items ?? [];
  const total = items.reduce((sum, item) => sum + (item.unit_price ?? 0) * item.quantity, 0);

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex items-center gap-6">
        <h1 className="font-display text-3xl">SACOLA</h1>
        <button
          onClick={() => setTab("favoritos")}
          className={`text-sm tracked uppercase ${tab === "favoritos" ? "text-[var(--ink)]" : "text-[var(--text-muted)]"}`}
        >
          Favoritos
        </button>
      </div>

      {tab === "favoritos" ? (
        <div className="mt-8">
          <EmptyState title="Você ainda não tem favoritos" description="Marque produtos na ficha para vê-los aqui." />
        </div>
      ) : items.length === 0 ? (
        <div className="mt-8">
          <EmptyState title="Sua sacola está vazia" description="Volte ao catálogo para adicionar produtos." />
          <Link to="/" className="mt-4 inline-block text-sm underline">
            Ir para o catálogo
          </Link>
        </div>
      ) : (
        <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            {items.map((item) => (
              <div key={item.id} className="flex gap-4 border-b border-[var(--border-hairline)] pb-6">
                <div className="flex h-24 w-20 shrink-0 items-center justify-center rounded-xl bg-[#e9e7e0] text-2xl">
                  👕
                </div>
                <div className="flex flex-1 flex-col justify-between">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium">{item.product_name ?? item.sku}</p>
                      <p className="text-xs text-[var(--text-muted)]">SKU {item.sku}</p>
                    </div>
                    <button onClick={() => removeItem(item.id)} className="text-[var(--text-muted)] hover:text-[var(--ink)]">
                      <IconX width={16} height={16} />
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 rounded-full border border-[var(--border-strong)] px-2 py-1">
                      <button
                        onClick={() => (item.quantity > 1 ? updateItem(item.id, item.quantity - 1) : removeItem(item.id))}
                        className="flex h-5 w-5 items-center justify-center"
                      >
                        <IconMinus width={13} height={13} />
                      </button>
                      <span className="w-4 text-center text-sm">{item.quantity}</span>
                      <button onClick={() => updateItem(item.id, item.quantity + 1)} className="flex h-5 w-5 items-center justify-center">
                        <IconPlus width={13} height={13} />
                      </button>
                    </div>
                    <p className="text-sm font-semibold">{formatCurrency((item.unit_price ?? 0) * item.quantity)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="h-fit rounded-2xl border border-[var(--border-hairline)] p-6">
            <p className="text-sm font-semibold tracked uppercase">Resumo do pedido</p>
            <div className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between text-[var(--text-secondary)]">
                <span>Subtotal</span>
                <span>{formatCurrency(total)}</span>
              </div>
              <div className="flex justify-between text-[var(--text-secondary)]">
                <span>Frete</span>
                <span>Calculado na próxima etapa</span>
              </div>
            </div>
            <div className="mt-4 flex justify-between border-t border-[var(--border-hairline)] pt-4 text-base font-semibold">
              <span>Total</span>
              <span>{formatCurrency(total)}</span>
            </div>
            <Button className="mt-6 w-full" onClick={() => navigate("/checkout")}>
              Continuar
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}