import { useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../../api/auth";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await forgotPassword(email);
    } finally {
      // Sempre mostra a mesma mensagem, exista ou não o e-mail (evita
      // confirmar quais e-mails estão cadastrados na base).
      setSent(true);
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="font-display text-3xl">ESQUECI MINHA SENHA</h1>

      <Card className="mt-6">
        {sent ? (
          <p className="text-sm text-[var(--text-secondary)]">
            Se este e-mail estiver cadastrado, enviamos um link de redefinição de senha. Verifique sua caixa de
            entrada (e o spam).
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            <p className="text-sm text-[var(--text-secondary)]">
              Informe o e-mail da sua conta para receber um link de redefinição de senha.
            </p>
            <input
              type="email"
              required
              placeholder="E-mail"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            />
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Enviando..." : "Enviar link de redefinição"}
            </Button>
          </form>
        )}
      </Card>

      <p className="mt-4 text-center text-sm text-[var(--text-secondary)]">
        <Link to="/login" className="underline">
          Voltar para o login
        </Link>
      </p>
    </div>
  );
}