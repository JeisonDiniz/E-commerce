import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchAddresses, addAddress } from "../../api/users";
import { checkout } from "../../api/orders";
import type { Address, PaymentMethod } from "../../types";
import { Button } from "../../components/ui/Button";
import { useCartStore } from "../../store/cartStore";
import { IconArrowRight } from "../../components/ui/icons";

const PAYMENT_OPTIONS: { value: PaymentMethod; label: string }[] = [
  { value: "pix", label: "Pix" },
  { value: "cartao_credito", label: "Cartão de crédito" },
  { value: "cartao_debito", label: "Cartão de débito" },
  { value: "boleto", label: "Boleto" },
];

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }).replace("R$", "$");
}

export function CheckoutPage() {
  const navigate = useNavigate();
  const { cart, clear, refresh } = useCartStore();

  const [step, setStep] = useState<"endereco" | "pagamento">("endereco");
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("pix");
  const [showNewAddress, setShowNewAddress] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    street: "",
    number: "",
    complement: "",
    neighborhood: "",
    city: "",
    state: "",
    zip_code: "",
  });

  useEffect(() => {
    refresh();
    fetchAddresses().then((list) => {
      setAddresses(list);
      if (list.length > 0) setSelectedAddressId(list[0].id);
      else setShowNewAddress(true);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const items = cart?.items ?? [];
  const subtotal = items.reduce((sum, item) => sum + (item.unit_price ?? 0) * item.quantity, 0);

  async function handleSaveAddress() {
    const address = await addAddress({ ...form, is_default: addresses.length === 0 });
    setAddresses((prev) => [...prev, address]);
    setSelectedAddressId(address.id);
    setShowNewAddress(false);
  }

  async function handleConfirm() {
    if (!selectedAddressId) {
      setError("Selecione ou cadastre um endereço de entrega.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const order = await checkout(selectedAddressId, paymentMethod);
      clear();
      navigate(`/meus-pedidos?confirmado=${order.id}`);
    } catch {
      setError("Não foi possível concluir o pedido. Verifique o estoque dos itens na sacola.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <button onClick={() => navigate("/carrinho")} className="mb-6 flex items-center gap-2 text-sm text-[var(--text-secondary)]">
        <IconArrowRight width={14} height={14} className="rotate-180" />
        Voltar
      </button>

      <h1 className="font-display text-3xl">Checkout</h1>

      <div className="mt-4 flex gap-6 border-b border-[var(--border-hairline)] pb-4 text-xs tracked uppercase">
        <button onClick={() => setStep("endereco")} className={step === "endereco" ? "text-[var(--ink)]" : "text-[var(--text-muted)]"}>
          Endereço
        </button>
        <button
          onClick={() => selectedAddressId && setStep("pagamento")}
          className={step === "pagamento" ? "text-[var(--ink)]" : "text-[var(--text-muted)]"}
        >
          Pagamento
        </button>
      </div>

      <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_340px]">
        <div>
          {step === "endereco" && (
            <div>
              <p className="text-sm font-semibold tracked uppercase">Endereço de entrega</p>
              <div className="mt-4 space-y-3">
                {addresses.map((addr) => (
                  <label
                    key={addr.id}
                    className="flex items-center gap-3 border-b border-[var(--border-hairline)] pb-3 text-sm"
                  >
                    <input type="radio" checked={selectedAddressId === addr.id} onChange={() => setSelectedAddressId(addr.id)} />
                    <span>
                      {addr.street}, {addr.number} — {addr.city}/{addr.state}
                    </span>
                  </label>
                ))}
              </div>

              {!showNewAddress ? (
                <button className="mt-4 text-sm underline" onClick={() => setShowNewAddress(true)}>
                  + Cadastrar novo endereço
                </button>
              ) : (
                <div className="mt-4 grid grid-cols-2 gap-x-4">
                  <input
                    className="field-underline col-span-2"
                    placeholder="Rua"
                    value={form.street}
                    onChange={(e) => setForm({ ...form, street: e.target.value })}
                  />
                  <input
                    className="field-underline"
                    placeholder="Número"
                    value={form.number}
                    onChange={(e) => setForm({ ...form, number: e.target.value })}
                  />
                  <input
                    className="field-underline"
                    placeholder="Bairro"
                    value={form.neighborhood}
                    onChange={(e) => setForm({ ...form, neighborhood: e.target.value })}
                  />
                  <input
                    className="field-underline"
                    placeholder="Cidade"
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                  />
                  <input
                    className="field-underline"
                    placeholder="UF"
                    maxLength={2}
                    value={form.state}
                    onChange={(e) => setForm({ ...form, state: e.target.value.toUpperCase() })}
                  />
                  <input
                    className="field-underline col-span-2"
                    placeholder="CEP"
                    value={form.zip_code}
                    onChange={(e) => setForm({ ...form, zip_code: e.target.value })}
                  />
                  <Button variant="secondary" className="col-span-2 mt-3" onClick={handleSaveAddress}>
                    Salvar endereço
                  </Button>
                </div>
              )}

              <Button className="mt-8" onClick={() => selectedAddressId && setStep("pagamento")} disabled={!selectedAddressId}>
                Continuar para pagamento
                <IconArrowRight width={16} height={16} />
              </Button>
            </div>
          )}

          {step === "pagamento" && (
            <div>
              <p className="text-sm font-semibold tracked uppercase">Forma de pagamento</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {PAYMENT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setPaymentMethod(opt.value)}
                    className={`rounded-full border px-4 py-2 text-sm ${
                      paymentMethod === opt.value ? "border-[var(--ink)] bg-[var(--ink)] text-white" : "border-[var(--border-strong)]"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              <label className="mt-6 flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
                Concordo com os termos e condições
              </label>

              {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

              <Button className="mt-6 w-full sm:w-auto" onClick={handleConfirm} disabled={submitting || !agreed}>
                {submitting ? "Processando..." : "Confirmar pedido"}
              </Button>
            </div>
          )}
        </div>

        <div className="h-fit rounded-2xl border border-[var(--border-hairline)] p-6">
          <p className="text-sm font-semibold tracked uppercase">Seu pedido</p>
          <div className="mt-4 space-y-4">
            {items.map((item) => (
              <div key={item.id} className="flex items-center gap-3 text-sm">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-[#e9e7e0] text-lg">👕</div>
                <div className="flex-1">
                  <p className="font-medium">{item.product_name ?? item.sku}</p>
                  <p className="text-xs text-[var(--text-muted)]">Qtd. {item.quantity}</p>
                </div>
                <p className="font-semibold">{formatCurrency((item.unit_price ?? 0) * item.quantity)}</p>
              </div>
            ))}
          </div>
          <div className="mt-5 space-y-2 border-t border-[var(--border-hairline)] pt-4 text-sm">
            <div className="flex justify-between text-[var(--text-secondary)]">
              <span>Subtotal</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
            <div className="flex justify-between text-[var(--text-secondary)]">
              <span>Frete</span>
              <span>Grátis</span>
            </div>
            <div className="flex justify-between border-t border-[var(--border-hairline)] pt-2 text-base font-semibold">
              <span>Total</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}