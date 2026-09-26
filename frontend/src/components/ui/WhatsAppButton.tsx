import { IconWhatsApp } from "./icons";

// TODO: trocar pelo número real da loja (código do país + DDD + número,
// só dígitos — ex.: 5511987654321). Enquanto for esse valor de exemplo, o
// botão continua visível mas não deve ser considerado funcional.
const WHATSAPP_NUMBER = "554796351565";
const DEFAULT_MESSAGE = "Olá! Vim do site e gostaria de tirar uma dúvida sobre um produto.";

/**
 * Botão flutuante fixo no canto inferior direito da loja, que abre uma
 * conversa no WhatsApp da loja numa aba nova (via link wa.me — não exige
 * nenhuma integração de API, só o número). Aparece só no site público
 * (StorefrontLayout); o painel admin não precisa dele.
 */
export function WhatsAppButton() {
  const href = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(DEFAULT_MESSAGE)}`;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      title="Falar no WhatsApp"
      aria-label="Falar no WhatsApp"
      className="fixed bottom-5 right-5 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--ink)] text-white shadow-lg transition-transform hover:scale-105 hover:bg-[var(--ink-soft)]"
    >
      <IconWhatsApp width={26} height={26} />
    </a>
  );
}
