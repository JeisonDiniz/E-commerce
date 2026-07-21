import { api } from "./client";
import type { Order, OrderStatus, PaymentMethod } from "../types";

export async function checkout(shippingAddressId: string, paymentMethod: PaymentMethod): Promise<Order> {
  const { data } = await api.post<Order>("/orders", {
    shipping_address_id: shippingAddressId,
    payment_method: paymentMethod,
  });
  return data;
}

export async function fetchMyOrders(): Promise<Order[]> {
  const { data } = await api.get<Order[]>("/orders/me");
  return data;
}

export async function fetchAllOrders(): Promise<Order[]> {
  const { data } = await api.get<Order[]>("/orders");
  return data;
}

export async function updateOrderStatus(orderId: string, status: OrderStatus): Promise<Order> {
  const { data } = await api.patch<Order>(`/orders/${orderId}/status`, null, { params: { new_status: status } });
  return data;
}