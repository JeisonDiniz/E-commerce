import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuthStore, isStaff } from "../../store/authStore";
import { useCartStore, cartItemCount } from "../../store/cartStore";
import { IconMenu, IconUser, IconBag, IconX } from "../ui/icons";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm transition-colors hover:text-[var(--ink)] ${isActive ? "text-[var(--ink)] font-semibold" : "text-[var(--text-secondary)]"}`;

export function StorefrontLayout() {
  const { user, logout } = useAuthStore();
  const { cart, refresh } = useCartStore();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  useEffect(() => {
    if (user) refresh();
  }, [user, refresh]);

  const closeMenu = () => setMenuOpen(false);
  const closeProfile = () => setProfileOpen(false);

  const handleLogout = () => {
    closeProfile();
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="h-[3px] bg-[var(--ink)]" />

      <header className="sticky top-0 z-20 bg-[var(--surface-page)]/95 backdrop-blur">
        <div className="flex w-full items-center justify-between px-6 py-5 md:px-10 lg:px-16">
          <div className="flex items-center gap-8">
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="text-[var(--ink)] sm:hidden"
              aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
              aria-expanded={menuOpen}
            >
              {menuOpen ? <IconX /> : <IconMenu />}
            </button>
            <nav className="hidden items-center gap-6 sm:flex">
              <NavLink to="/" end className={navLinkClass}>
                Início
              </NavLink>
              <NavLink to="/carrinho" className={navLinkClass}>
                Carrinho
              </NavLink>
              {user && (
                <NavLink to="/meus-pedidos" className={navLinkClass}>
                  Meus pedidos
                </NavLink>
              )}
              {isStaff(user) && (
                <NavLink to="/admin" className={navLinkClass}>
                  Painel admin
                </NavLink>
              )}
            </nav>
          </div>

          <Link to="/" className="font-display text-lg">
            LV
          </Link>

          <div className="flex items-center gap-2">
            <Link
              to="/carrinho"
              className="relative flex h-10 items-center gap-2 rounded-full bg-[var(--ink)] pl-4 pr-1.5 text-sm font-medium text-white"
            >
              Sacola
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-[var(--ink)]">
                <IconBag width={15} height={15} />
              </span>
              {cartItemCount(cart) > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-white text-[10px] font-semibold text-[var(--ink)] ring-2 ring-[var(--surface-page)]">
                  {cartItemCount(cart)}
                </span>
              )}
            </Link>

            {user ? (
              <div className="relative">
                <button
                  onClick={() => setProfileOpen((v) => !v)}
                  title={user.name}
                  aria-haspopup="menu"
                  aria-expanded={profileOpen}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--ink)] text-white"
                >
                  <IconUser />
                </button>

                {profileOpen && (
                  <>
                    <button
                      className="fixed inset-0 z-10 cursor-default bg-transparent"
                      onClick={closeProfile}
                      aria-hidden="true"
                      tabIndex={-1}
                    />
                    <div
                      role="menu"
                      className="absolute right-0 top-12 z-20 w-52 rounded-2xl border border-[var(--border-hairline)] bg-[var(--surface-card)] py-2 shadow-lg"
                    >
                      <p className="truncate px-4 py-2 text-xs text-[var(--text-muted)]">{user.name}</p>
                      <NavLink
                        to="/meus-pedidos"
                        onClick={closeProfile}
                        className="block px-4 py-2 text-sm hover:bg-neutral-100"
                      >
                        Meus pedidos
                      </NavLink>
                      {isStaff(user) && (
                        <NavLink
                          to="/admin"
                          onClick={closeProfile}
                          className="block px-4 py-2 text-sm hover:bg-neutral-100"
                        >
                          Painel admin
                        </NavLink>
                      )}
                      <button
                        onClick={handleLogout}
                        className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-neutral-100"
                      >
                        Sair
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <Link to="/login" className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--ink)] text-white">
                <IconUser />
              </Link>
            )}
          </div>
        </div>

        {menuOpen && (
          <>
            <button className="fixed inset-0 z-10 cursor-default bg-black/10" onClick={closeMenu} aria-hidden="true" tabIndex={-1} />
            <nav className="relative z-20 flex flex-col gap-1 border-t border-[var(--border-hairline)] bg-[var(--surface-card)] px-6 py-4 md:px-10 lg:px-16">
              <NavLink to="/" end onClick={closeMenu} className="rounded-lg px-3 py-2 text-sm hover:bg-neutral-100">
                Início
              </NavLink>
              <NavLink to="/carrinho" onClick={closeMenu} className="rounded-lg px-3 py-2 text-sm hover:bg-neutral-100">
                Carrinho
              </NavLink>
              {user ? (
                <>
                  <NavLink to="/meus-pedidos" onClick={closeMenu} className="rounded-lg px-3 py-2 text-sm hover:bg-neutral-100">
                    Meus pedidos
                  </NavLink>
                  {isStaff(user) && (
                    <NavLink to="/admin" onClick={closeMenu} className="rounded-lg px-3 py-2 text-sm hover:bg-neutral-100">
                      Painel admin
                    </NavLink>
                  )}
                  <button
                    onClick={() => {
                      closeMenu();
                      handleLogout();
                    }}
                    className="rounded-lg px-3 py-2 text-left text-sm hover:bg-neutral-100"
                  >
                    Sair ({user.name.split(" ")[0]})
                  </button>
                </>
              ) : (
                <>
                  <NavLink to="/login" onClick={closeMenu} className="rounded-lg px-3 py-2 text-sm hover:bg-neutral-100">
                    Entrar
                  </NavLink>
                  <NavLink to="/cadastro" onClick={closeMenu} className="rounded-lg px-3 py-2 text-sm hover:bg-neutral-100">
                    Criar conta
                  </NavLink>
                </>
              )}
            </nav>
          </>
        )}
      </header>

      <main className="w-full flex-1 px-6 py-8 md:px-10 lg:px-16">
        <Outlet />
      </main>

      <footer className="border-t border-[var(--border-hairline)] py-6 text-center text-xs tracked text-[var(--text-muted)]">
        PROJETO DE TCC — LOJA VIRTUAL COM ESTOQUE INTELIGENTE E MACHINE LEARNING
      </footer>
    </div>
  );
}