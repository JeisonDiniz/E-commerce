import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login, fetchMe } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { PasswordInput } from "../../components/ui/PasswordInput";

export function LoginPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { access_token } = await login(email, password);
      useAuthStore.setState({ token: access_token });
      const user = await fetchMe();
      setSession(access_token, user);
      navigate("/");
    } catch {
      setError("E-mail ou senha inválidos.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="font-display text-3xl">Entrar</h1>
      <Card className="mt-6">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="login-email" className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">
              E-mail
            </label>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              placeholder="E-mail"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            />
          </div>

          <PasswordInput
            label="Senha"
            required
            autoComplete="current-password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
          />

          <div className="text-right">
            <Link to="/esqueci-senha" className="text-xs text-[var(--text-secondary)] underline">
              Esqueci minha senha
            </Link>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Entrando..." : "Entrar"}
          </Button>
        </form>
      </Card>
      <p className="mt-4 text-center text-sm text-[var(--text-secondary)]">
        Não tem conta?{" "}
        <Link to="/cadastro" className="underline">
          Cadastre-se
        </Link>
      </p>
      <p className="mt-2 text-center text-xs text-[var(--text-muted)]">
        Contas de demonstração (após rodar o seed): admin@loja.com / gestor@loja.com / estoque@loja.com — senha Senha@123
      </p>
    </div>
  );
}