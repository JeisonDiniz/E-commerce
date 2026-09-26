import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchMyOrders } from "../../api/orders";
import type { Order } from "../../types";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Spinner } from "../../components/ui/Spinner";
import { EmptyState } from "../../components/ui/EmptyState";
import { formatCurrency } from "../../utils/currency";

const STATUS_BADGE: Record<Order["status"], { status: "good" | "warning" | "critical" | "neutral"; label: string }> = {
  pendente: { status: "neutral", label: "Pendente" },
  pago: { status: "good", label: "Pago" },
  processando: { status: "warning", label: "Processando" },
  enviado: { status: "warning", label: "Enviado" },
  entregue: { status: "good", label: "Entregue" },
  cancelado: { status: "critical", label: "Cancelado" },
};

export function OrdersHistoryPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [params] = useSearchParams();
  const confirmedId = params.get("confirmado");

  useEffect(() => {
    fetchMyOrders()
      .then(setOrders)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-display text-3xl">MEUS PEDIDOS</h1>

      {confirmedId && (
        <p className="mt-3 rounded-md bg-green-50 px-3 py-2 text-sm text-green-800">
          Pedido confirmado com sucesso!
        </p>
      )}

      {orders.length === 0 ? (
        <div className="mt-6">
          <EmptyState title="Você ainda não fez nenhum pedido" />
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {orders.map((order) => (
            <Card key={order.id}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Pedido #{order.id.slice(0, 8)}</p>
                  <p className="text-xs text-[var(--text-muted)]">
                    {new Date(order.created_at).toLocaleDateString("pt-BR")} · {order.items.length} item(ns)
                  </p>
                </div>
                <div className="text-right">
                  <Badge status={STATUS_BADGE[order.status].status} label={STATUS_BADGE[order.status].label} />
                  <p className="mt-1 text-sm font-semibold">{formatCurrency(order.total_amount)}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}