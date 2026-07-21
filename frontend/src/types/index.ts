// Tipos espelhando os schemas Pydantic do back-end (backend/app/schemas/*.py).
// Mantidos manualmente (sem geração automática) para simplicidade do TCC —
// qualquer mudança nos schemas do back-end deve ser refletida aqui.

export type UserRole = "customer" | "staff" | "manager" | "admin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Address {
  id: string;
  user_id: string;
  street: string;
  number: string;
  complement?: string | null;
  neighborhood: string;
  city: string;
  state: string;
  zip_code: string;
  is_default: boolean;
}

export type GenderType = "masculino" | "feminino" | "unissex" | "infantil";
export type SeasonType = "verao" | "inverno" | "outono" | "primavera" | "o_ano_todo";
export type SizeType = "PP" | "P" | "M" | "G" | "GG" | "XG" | "UNICO" | "34" | "36" | "38" | "40" | "42" | "44" | "46" | "48";

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id?: string | null;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  sku: string;
  size: SizeType;
  color: string;
  price: number;
  cost_price?: number | null;
  active: boolean;
  stock_quantity: number | null;
}

export interface Product {
  id: string;
  category_id: string;
  name: string;
  description?: string | null;
  brand?: string | null;
  gender: GenderType;
  season: SeasonType;
  base_price: number;
  active: boolean;
  variants: ProductVariant[];
}

export type MovementType = "entrada" | "saida" | "ajuste" | "devolucao";

export interface InventoryMovement {
  id: string;
  variant_id: string;
  movement_type: MovementType;
  quantity: number;
  reason?: string | null;
  reference_order_id?: string | null;
  created_by?: string | null;
  created_at: string;
}

export interface LowStockItem {
  variant_id: string;
  sku: string;
  product_name: string;
  quantity: number;
  min_quantity: number;
}

export interface CartItem {
  id: string;
  variant_id: string;
  quantity: number;
  sku?: string | null;
  product_name?: string | null;
  unit_price?: number | null;
}

export interface Cart {
  id: string;
  user_id: string;
  items: CartItem[];
}

export type OrderStatus = "pendente" | "pago" | "processando" | "enviado" | "entregue" | "cancelado";
export type PaymentMethod = "cartao_credito" | "cartao_debito" | "pix" | "boleto";

export interface OrderItem {
  id: string;
  variant_id: string;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: string;
  user_id: string;
  shipping_address_id: string;
  status: OrderStatus;
  total_amount: number;
  created_at: string;
  items: OrderItem[];
}

export type ModelType = "prophet" | "random_forest";

export interface MLPrediction {
  id: string;
  model_type: ModelType;
  variant_id?: string | null;
  category_id?: string | null;
  prediction_date: string;
  predicted_quantity: number;
  confidence_lower?: number | null;
  confidence_upper?: number | null;
  model_version: string;
  generated_at: string;
}

export interface MLModelMetric {
  id: string;
  model_type: ModelType;
  model_version: string;
  mae: number;
  mape: number;
  rmse?: number | null;
  training_samples: number;
  trained_at: string;
  notes?: string | null;
}

export type SuggestionStatus = "pendente" | "aprovada" | "rejeitada";

export interface RestockSuggestion {
  id: string;
  variant_id: string;
  based_on_prediction_id?: string | null;
  suggested_quantity: number;
  status: SuggestionStatus;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface DailySalesPoint {
  sale_date: string;
  units_sold: number;
  revenue: number;
}

export interface TopProduct {
  product_name: string;
  sku: string;
  units_sold: number;
  revenue: number;
}

export interface InventoryStatusSummary {
  total_variants: number;
  total_units_in_stock: number;
  variants_below_min: number;
}