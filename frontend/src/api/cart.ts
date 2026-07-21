import { api } from "./client";
import type { Cart } from "../types";

export async function fetchCart(): Promise<Cart> {
  const { data } = await api.get<Cart>("/cart");
  return data;
}

export async function addCartItem(variantId: string, quantity: number): Promise<Cart> {
  const { data } = await api.post<Cart>("/cart/items", { variant_id: variantId, quantity });
  return data;
}

export async function updateCartItem(itemId: string, quantity: number): Promise<Cart> {
  const { data } = await api.patch<Cart>(`/cart/items/${itemId}`, { quantity });
  return data;
}

export async function removeCartItem(itemId: string): Promise<void> {
  await api.delete(`/cart/items/${itemId}`);
}