import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router";
import { useAdminAuthStore } from "@/stores/adminAuth";

export async function requireAdminAuth(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
): Promise<void> {
  const authStore = useAdminAuthStore();
  await authStore.initialize();
  if (authStore.isAuthenticated) {
    next();
    return;
  }
  next({ name: "admin-login", query: { redirect: _to.fullPath } });
}

export async function redirectAuthenticatedAdmin(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
): Promise<void> {
  const authStore = useAdminAuthStore();
  await authStore.initialize();
  if (authStore.isAuthenticated) {
    next({ name: "admin-home" });
    return;
  }
  next();
}
