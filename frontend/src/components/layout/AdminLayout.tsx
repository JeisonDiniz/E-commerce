import { Link, NavLink, Outlet } from "react-router-dom";
import { useState } from "react";
import { useAuthStore } from "../../store/authStore";
import { IconMenu, IconX } from "../ui/icons";
import { ThemeToggle } from "../ui/ThemeToggle";

const NAV_ITEMS = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/produtos", label: "Produtos" },
  { to: "/admin/estoque", label: "Estoque" },
  { to: "/admin/reposicao", label: "Sugestões de reposição" },
  { to: "/admin/pedidos", label: "Pedidos" },
];

export function AdminLayout() {
  const { user } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);

  const navLinks = (onNavigate?: () => void) => (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `rounded-md px-3 py-2 text-sm font-medium ${
              isActive ? "bg-neutral-900 text-white" : "text-[var(--text-secondary)] hover:bg-neutral-100"
            }`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      {/* Topo mobile: some a partir de md, onde a sidebar fixa assume */}
      <div className="flex items-center justify-between border-b border-[var(--border-hairline)] bg-[var(--surface-card)] p-4 md:hidden">
        <Link to="/" className="text-sm font-semibold">
          ← Voltar à loja
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Abrir menu do painel"
            aria-expanded={menuOpen}
            className="text-[var(--ink)]"
          >
            {menuOpen ? <IconX /> : <IconMenu />}
          </button>
        </div>
      </div>
      {menuOpen && (
        <div className="border-b border-[var(--border-hairline)] bg-[var(--surface-card)] p-4 md:hidden">
          <p className="mb-3 text-xs text-[var(--text-muted)]">
            Logado como {user?.name} ({user?.role})
          </p>
          {navLinks(() => setMenuOpen(false))}
        </div>
      )}

      {/* Sidebar fixa em telas médias/grandes */}
      <aside className="hidden w-60 shrink-0 border-r border-[var(--border-hairline)] bg-[var(--surface-card)] p-4 md:block">
        <div className="mb-6 flex items-center justify-between">
          <Link to="/" className="text-sm font-semibold">
            ← Voltar à loja
          </Link>
          <ThemeToggle />
        </div>
        <p className="mb-4 text-xs text-[var(--text-muted)]">
          Logado como {user?.name} ({user?.role})
        </p>
        {navLinks()}
      </aside>

      <main className="min-w-0 flex-1 overflow-x-auto p-4 sm:p-6 md:p-8">
        <Outlet />
      </main>
    </div>
  );
}