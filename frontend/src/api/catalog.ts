import { api } from "./client";
import type { Category, GenderType, Product, SeasonType } from "../types";

export async function fetchCategories(): Promise<Category[]> {
  const { data } = await api.get<Category[]>("/categories");
  return data;
}

export interface ProductFilters {
  category_id?: string;
  gender?: GenderType;
  season?: SeasonType;
  skip?: number;
  limit?: number;
}

export async function fetchProducts(filters: ProductFilters = {}): Promise<Product[]> {
  const { data } = await api.get<Product[]>("/products", { params: filters });
  return data;
}

export async function fetchProduct(productId: string): Promise<Product> {
  const { data } = await api.get<Product>(`/products/${productId}`);
  return data;
}