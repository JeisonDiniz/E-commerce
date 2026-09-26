import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { StorefrontLayout } from "./components/layout/StorefrontLayout";
import { AdminLayout } from "./components/layout/AdminLayout";
import { RequireAuth, RequireStaff } from "./routes/ProtectedRoute";
import { Spinner } from "./components/ui/Spinner";

// Code-splitting por rota: cada página vira um chunk JS separado, baixado só
// quando a rota é visitada. Antes disso, o bundle inteiro (loja + admin +
// gráficos do dashboard, que puxam a recharts) ia tudo junto num único
// arquivo de ~750KB — a maioria dos visitantes da loja nunca abre o painel
// admin, então não faz sentido eles baixarem esse código de antemão.
const HomePage = lazy(() => import("./pages/storefront/HomePage").then((m) => ({ default: m.HomePage })));
const ProductDetailPage = lazy(() =>
  import("./pages/storefront/ProductDetailPage").then((m) => ({ default: m.ProductDetailPage }))
);
const CartPage = lazy(() => import("./pages/storefront/CartPage").then((m) => ({ default: m.CartPage })));
const CheckoutPage = lazy(() => import("./pages/storefront/CheckoutPage").then((m) => ({ default: m.CheckoutPage })));
const OrdersHistoryPage = lazy(() =>
  import("./pages/storefront/OrdersHistoryPage").then((m) => ({ default: m.OrdersHistoryPage }))
);
const LoginPage = lazy(() => import("./pages/storefront/LoginPage").then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("./pages/storefront/RegisterPage").then((m) => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(() =>
  import("./pages/storefront/ForgotPasswordPage").then((m) => ({ default: m.ForgotPasswordPage }))
);
const ResetPasswordPage = lazy(() =>
  import("./pages/storefront/ResetPasswordPage").then((m) => ({ default: m.ResetPasswordPage }))
);

const DashboardPage = lazy(() => import("./pages/admin/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const ProductsAdminPage = lazy(() =>
  import("./pages/admin/ProductsAdminPage").then((m) => ({ default: m.ProductsAdminPage }))
);
const InventoryAdminPage = lazy(() =>
  import("./pages/admin/InventoryAdminPage").then((m) => ({ default: m.InventoryAdminPage }))
);
const RestockSuggestionsPage = lazy(() =>
  import("./pages/admin/RestockSuggestionsPage").then((m) => ({ default: m.RestockSuggestionsPage }))
);
const OrdersAdminPage = lazy(() => import("./pages/admin/OrdersAdminPage").then((m) => ({ default: m.OrdersAdminPage })));

function PageFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <Spinner />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route element={<StorefrontLayout />}>
            <Route index element={<HomePage />} />
            <Route path="produtos/:productId" element={<ProductDetailPage />} />
            <Route path="carrinho" element={<CartPage />} />
            <Route
              path="checkout"
              element={
                <RequireAuth>
                  <CheckoutPage />
                </RequireAuth>
              }
            />
            <Route
              path="meus-pedidos"
              element={
                <RequireAuth>
                  <OrdersHistoryPage />
                </RequireAuth>
              }
            />
            <Route path="login" element={<LoginPage />} />
            <Route path="cadastro" element={<RegisterPage />} />
            <Route path="esqueci-senha" element={<ForgotPasswordPage />} />
            <Route path="redefinir-senha" element={<ResetPasswordPage />} />
          </Route>

          <Route
            path="admin"
            element={
              <RequireStaff>
                <AdminLayout />
              </RequireStaff>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="produtos" element={<ProductsAdminPage />} />
            <Route path="estoque" element={<InventoryAdminPage />} />
            <Route path="reposicao" element={<RestockSuggestionsPage />} />
            <Route path="pedidos" element={<OrdersAdminPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
