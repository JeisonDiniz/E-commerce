import { api } from "./client";
import type { DailySalesPoint, InventoryStatusSummary, TopProduct } from "../types";

export async function fetchSalesSummary(startDate?: string, endDate?: string): Promise<DailySalesPoint[]> {
  const { data } = await api.get<DailySalesPoint[]>("/reports/sales-summary", {
    params: { start_date: startDate, end_date: endDate },
  });
  return data;
}

export async function fetchTopProducts(limit = 10): Promise<TopProduct[]> {
  const { data } = await api.get<TopProduct[]>("/reports/top-products", { params: { limit } });
  return data;
}

export async function fetchInventoryStatus(): Promise<InventoryStatusSummary> {
  const { data } = await api.get<InventoryStatusSummary>("/reports/inventory-status");
  return data;
}