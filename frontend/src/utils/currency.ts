// Utilitário único de formatação monetária — evita ter a mesma função
// (e o mesmo tipo de bug) duplicada em cada página. Aceita number | string
// porque APIs que serializam Decimal como texto (ou qualquer futura
// mudança de contrato) não devem voltar a quebrar a exibição do preço.
export function formatCurrency(value: number | string): string {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
