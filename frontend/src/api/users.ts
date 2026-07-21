import { api } from "./client";
import type { Address } from "../types";

export type AddressInput = Omit<Address, "id" | "user_id">;

export async function fetchAddresses(): Promise<Address[]> {
  const { data } = await api.get<Address[]>("/users/me/addresses");
  return data;
}

export async function addAddress(payload: AddressInput): Promise<Address> {
  const { data } = await api.post<Address>("/users/me/addresses", payload);
  return data;
}
