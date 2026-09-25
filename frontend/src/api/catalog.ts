import { api } from "./client";
import type { Category, GenderType, Product, ProductImage, SeasonType } from "../types";

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

export async function uploadProductImage(
  productId: string,
  file: File,
  color: string | null,
  isPrimary = false
): Promise<ProductImage> {
  const form = new FormData();
  form.append("file", file);
  if (color) form.append("color", color);
  form.append("is_primary", String(isPrimary));

  const { data } = await api.post<ProductImage>(`/products/${productId}/images`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteProductImage(productId: string, imageId: string): Promise<void> {
  await api.delete(`/products/${productId}/images/${imageId}`);
}