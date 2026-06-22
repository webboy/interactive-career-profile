import { flushPromises, mount } from "@vue/test-utils";
import { QLayout, QPageContainer } from "quasar";
import { describe, expect, it, vi } from "vitest";
import AdminLoginPage from "@/pages/admin/AdminLoginPage.vue";
import { i18n } from "@/i18n";

const push = vi.fn();

vi.mock("vue-router", () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push }),
}));

vi.mock("@/stores/adminAuth", () => ({
  useAdminAuthStore: () => ({
    login: vi.fn(async (email: string, password: string) => email.includes("@") && password.length > 0),
    error: null,
    loading: false,
  }),
}));

describe("AdminLoginPage", () => {
  it("submits credentials and redirects to admin home", async () => {
    const wrapper = mount(
      {
        components: { QLayout, QPageContainer, AdminLoginPage },
        template: "<q-layout><q-page-container><AdminLoginPage /></q-page-container></q-layout>",
      },
      {
        global: { plugins: [i18n] },
      },
    );

    await wrapper.find('input[type="email"]').setValue("demo-admin@example.com");
    await wrapper.find('input[type="password"]').setValue("change-me-demo-password");
    await wrapper.find("button").trigger("click");
    await flushPromises();

    expect(push).toHaveBeenCalledWith("/admin");
  });
});
