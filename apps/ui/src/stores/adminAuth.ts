import { defineStore } from "pinia";
import { getCurrentUser, login as apiLogin, logout as apiLogout } from "@/api/auth";
import type { UserResponse } from "@/api/types";

export const useAdminAuthStore = defineStore("adminAuth", {
  state: () => ({
    user: null as UserResponse | null,
    loading: false,
    error: null as string | null,
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => state.user !== null,
  },
  actions: {
    async initialize(): Promise<void> {
      if (this.initialized) {
        return;
      }
      await this.refresh();
      this.initialized = true;
    },
    async refresh(): Promise<UserResponse | null> {
      this.loading = true;
      this.error = null;
      try {
        this.user = await getCurrentUser();
        return this.user;
      } catch (error) {
        this.user = null;
        this.error = error instanceof Error ? error.message : "Failed to load session";
        return null;
      } finally {
        this.loading = false;
      }
    },
    async login(email: string, password: string): Promise<boolean> {
      this.loading = true;
      this.error = null;
      try {
        this.user = await apiLogin(email, password);
        return true;
      } catch (error) {
        this.user = null;
        this.error = error instanceof Error ? error.message : "Login failed";
        return false;
      } finally {
        this.loading = false;
      }
    },
    async logout(): Promise<void> {
      this.loading = true;
      this.error = null;
      try {
        await apiLogout();
      } finally {
        this.user = null;
        this.loading = false;
      }
    },
  },
});
