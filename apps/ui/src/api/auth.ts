import { apiRequest } from "./client";
import { ApiError } from "./types";

export async function login(email: string, password: string) {
  return apiRequest<{ id: number; email: string; is_active: boolean }>(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
    { credentials: "include" },
  );
}

export async function logout(): Promise<void> {
  await apiRequest<void>("/api/auth/logout", { method: "POST" }, { credentials: "include" });
}

export async function getCurrentUser() {
  try {
    return await apiRequest<{ id: number; email: string; is_active: boolean }>(
      "/api/auth/me",
      {},
      { credentials: "include" },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}
