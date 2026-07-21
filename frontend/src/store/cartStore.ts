import { create } from "zustand";
import * as cartApi from "../api/cart";
import type { Cart } from "../types";

interface CartState {
  cart: Cart | null;
  loading: boolean;
  refresh: () => Promise<void>;
  addItem: (variantId: string, quantity: number) => Promise<void>;
  updateItem: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clear: () => void;
}

export const useCartStore = create<CartState>((set, get) => ({
  cart: null,
  loading: false,

  refresh: async () => {
    set({ loading: true });
    try {
      const cart = await cartApi.fetchCart();
      set({ cart });
    } finally {
      set({ loading: false });
    }
  },

  addItem: async (variantId, quantity) => {
    const cart = await cartApi.addCartItem(variantId, quantity);
    set({ cart });
  },

  updateItem: async (itemId, quantity) => {
    const cart = await cartApi.updateCartItem(itemId, quantity);
    set({ cart });
  },

  removeItem: async (itemId) => {
    await cartApi.removeCartItem(itemId);
    await get().refresh();
  },

  clear: () => set({ cart: null }),
}));

export function cartItemCount(cart: Cart | null): number {
  if (!cart) return 0;
  return cart.items.reduce((sum, item) => sum + item.quantity, 0);
}