import type { PropsWithChildren } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore, isStaff } from "../store/authStore";

export function RequireAuth({ children }: PropsWithChildren) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function RequireStaff({ children }: PropsWithChildren) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  if (!isStaff(user)) return <Navigate to="/" replace />;
  return <>{children}</>;
}