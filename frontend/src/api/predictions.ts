import { api } from "./client";
import type { MLModelMetric, MLPrediction, RestockSuggestion, SuggestionStatus } from "../types";

export async function fetchCategoryPredictions(categoryId: string): Promise<MLPrediction[]> {
  const { data } = await api.get<MLPrediction[]>(`/predictions/categories/${categoryId}`);
  return data;
}

export async function fetchVariantPredictions(variantId: string): Promise<MLPrediction[]> {
  const { data } = await api.get<MLPrediction[]>(`/predictions/variants/${variantId}`);
  return data;
}

export async function fetchModelMetrics(): Promise<MLModelMetric[]> {
  const { data } = await api.get<MLModelMetric[]>("/ml/metrics");
  return data;
}

export async function fetchRestockSuggestions(status?: SuggestionStatus): Promise<RestockSuggestion[]> {
  const { data } = await api.get<RestockSuggestion[]>("/restock-suggestions", {
    params: status ? { suggestion_status: status } : {},
  });
  return data;
}

export async function reviewRestockSuggestion(id: string, approve: boolean): Promise<RestockSuggestion> {
  const { data } = await api.post<RestockSuggestion>(`/restock-suggestions/${id}/review`, { approve });
  return data;
}