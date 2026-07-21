import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register, login, fetchMe } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { PasswordInput } from "../../components/ui/PasswordInput";

export function RegisterPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (form.password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }

    setSubmitting(true);
    try {
      await register(form);
      const { access_token } = await login(form.email, form.password);
      useAuthStore.setState({ token: access_token });
      const user = await fetchMe();
      setSession(access_token, user);
      navigate("/");
    } catch {
      setError("Não foi possível criar a conta. Verifique se o e-mail já está em uso.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="font-display text-3xl">Criar conta</h1>
      <Card className="mt-6">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="register-name" className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">
              Nome
            </label>
            <input
              id="register-name"
              required
              autoComplete="name"
              placeholder="Nome"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label htmlFor="register-email" className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">
              E-mail
            </label>
            <input
              id="register-email"
              type="email"
              required
              autoComplete="email"
              placeholder="E-mail"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            />
          </div>

          <PasswordInput
            label="Senha"
            required
            minLength={6}
            autoComplete="new-password"
            placeholder="Senha"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
          />

          <PasswordInput
            label="Confirmar senha"
            required
            minLength={6}
            autoComplete="new-password"
            placeholder="Confirmar senha"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm"
          />

          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Criando..." : "Criar conta"}
          </Button>
        </form>
      </Card>
    </div>
  );
}