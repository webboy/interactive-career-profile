import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAdminAuthStore } from "@/stores/adminAuth";

vi.mock("@/api/auth", () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));

describe("admin auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("marks user authenticated after successful login", async () => {
    const { login } = await import("@/api/auth");
    vi.mocked(login).mockResolvedValue({
      id: 1,
      email: "admin@example.com",
      is_active: true,
    });

    const store = useAdminAuthStore();
    const ok = await store.login("admin@example.com", "secret");

    expect(ok).toBe(true);
    expect(store.isAuthenticated).toBe(true);
    expect(store.user?.email).toBe("admin@example.com");
  });

  it("clears user on logout", async () => {
    const { logout } = await import("@/api/auth");
    vi.mocked(logout).mockResolvedValue(undefined);

    const store = useAdminAuthStore();
    store.user = { id: 1, email: "admin@example.com", is_active: true };
    await store.logout();

    expect(store.isAuthenticated).toBe(false);
    expect(logout).toHaveBeenCalled();
  });
});
