import { api } from "./client";
import type { InventoryMovement, LowStockItem, MovementType } from "../types";

export async function fetchLowStock(): Promise<LowStockItem[]> {
  const { data } = await api.get<LowStockItem[]>("/inventory/low-stock");
  return data;
}

export async function createMovement(payload: {
  variant_id: string;
  movement_type: MovementType;
  quantity: number;
  reason?: string;
}): Promise<InventoryMovement> {
  const { data } = await api.post<InventoryMovement>("/inventory/movements", payload);
  return data;
}
