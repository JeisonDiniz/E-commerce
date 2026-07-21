import { useEffect, useState } from "react";
import { fetchAllOrders, updateOrderStatus } from "../../api/orders";
import type { Order, OrderStatus } from "../../types";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Spinner } from "../../components/ui/Spinner";

const STATUS_OPTIONS: OrderStatus[] = ["pendente", "pago", "processando", "enviado", "entregue", "cancelado"];

const STATUS_BADGE: Record<OrderStatus, { status: "good" | "warning" | "critical" | "neutral"; label: string }> = {
  pendente: { status: "neutral", label: "Pendente" },
  pago: { status: "good", label: "Pago" },
  processando: { status: "warning", label: "Processando" },
  enviado: { status: "warning", label: "Enviado" },
  entregue: { status: "good", label: "Entregue" },
  cancelado: { status: "critical", label: "Cancelado" },
};

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function OrdersAdminPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    fetchAllOrders()
      .then(setOrders)
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleStatusChange(orderId: string, status: OrderStatus) {
    await updateOrderStatus(orderId, status);
    load();
  }

  if (loading) return <Spinner />;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Pedidos</h1>
      <Card className="mt-4">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border-hairline)] text-xs text-[var(--text-muted)]">
              <th className="pb-2">Pedido</th>
              <th className="pb-2">Data</th>
              <th className="pb-2">Total</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Alterar</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id} className="border-b border-[var(--border-hairline)] last:border-0">
                <td className="py-2 text-xs text-[var(--text-muted)]">#{order.id.slice(0, 8)}</td>
                <td className="py-2">{new Date(order.created_at).toLocaleDateString("pt-BR")}</td>
                <td className="py-2 font-medium">{formatCurrency(order.total_amount)}</td>
                <td className="py-2">
                  <Badge status={STATUS_BADGE[order.status].status} label={STATUS_BADGE[order.status].label} />
                </td>
                <td className="py-2">
                  <select
                    value={order.status}
                    onChange={(e) => handleStatusChange(order.id, e.target.value as OrderStatus)}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-xs"
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
