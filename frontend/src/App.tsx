import { BrowserRouter, Route, Routes } from "react-router-dom";
import { StorefrontLayout } from "./components/layout/StorefrontLayout";
import { AdminLayout } from "./components/layout/AdminLayout";
import { RequireAuth, RequireStaff } from "./routes/ProtectedRoute";

import { HomePage } from "./pages/storefront/HomePage";
import { ProductDetailPage } from "./pages/storefront/ProductDetailPage";
import { CartPage } from "./pages/storefront/CartPage";
import { CheckoutPage } from "./pages/storefront/CheckoutPage";
import { OrdersHistoryPage } from "./pages/storefront/OrdersHistoryPage";
import { LoginPage } from "./pages/storefront/LoginPage";
import { RegisterPage } from "./pages/storefront/RegisterPage";
import { ForgotPasswordPage } from "./pages/storefront/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/storefront/ResetPasswordPage";

import { DashboardPage } from "./pages/admin/DashboardPage";
import { ProductsAdminPage } from "./pages/admin/ProductsAdminPage";
import { InventoryAdminPage } from "./pages/admin/InventoryAdminPage";
import { RestockSuggestionsPage } from "./pages/admin/RestockSuggestionsPage";
import { OrdersAdminPage } from "./pages/admin/OrdersAdminPage";

export default function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}
