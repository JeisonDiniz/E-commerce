import { api } from "./client";
import type { Category, GenderType, Product, ProductImage, SeasonType, SizeType } from "../types";

export async function fetchCategories(): Promise<Category[]> {
  const { data } = await api.get<Category[]>("/categories");
  return data;
}

export async function createCategory(name: string): Promise<Category> {
  // Slug gerado a partir do nome (minúsculo, espaços e acentos fora) — quem
  // cadastra uma categoria rápido no meio do cadastro de produto não deveria
  // precisar pensar em "slug", só no nome.
  const slug = name
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

  const { data } = await api.post<Category>("/categories", { name, slug });
  return data;
}

export interface ProductVariantInput {
  sku?: string;
  size: SizeType;
  color: string;
  price: number;
}

export interface ProductInput {
  category_id: string;
  name: string;
  brand?: string;
  gender: GenderType;
  season: SeasonType;
  base_price: number;
  variants: ProductVariantInput[];
}

export async function createProduct(payload: ProductInput): Promise<Product> {
  const { data } = await api.post<Product>("/products", payload);
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