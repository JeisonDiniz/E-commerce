// Mapeia os nomes de cor em português (cadastrados no catálogo) para hex,
// só para exibir os "swatches" de cor na UI — não é uma taxonomia de cores.
const COLOR_HEX: Record<string, string> = {
  Preto: "#111111",
  Branco: "#ffffff",
  "Azul Marinho": "#1c2f4a",
  "Cinza Mescla": "#9a9a95",
  Vermelho: "#b3372c",
  "Verde Militar": "#556b45",
  Bege: "#e3d5bc",
  Rosa: "#e3a8b8",
};

export function colorToHex(name: string): string {
  return COLOR_HEX[name] ?? "#9a9a95";
}