import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const NAV_ITEMS = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/produtos", label: "Produtos" },
  { to: "/admin/estoque", label: "Estoque" },
  { to: "/admin/reposicao", label: "Sugestões de reposição" },
  { to: "/admin/pedidos", label: "Pedidos" },
];

export function AdminLayout() {
  const { user } = useAuthStore();

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 border-r border-[var(--border-hairline)] bg-[var(--surface-card)] p-4">
        <Link to="/" className="mb-6 block text-sm font-semibold">
          ← Voltar à loja
        </Link>
        <p className="mb-4 text-xs text-[var(--text-muted)]">Logado como {user?.name} ({user?.role})</p>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
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
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}