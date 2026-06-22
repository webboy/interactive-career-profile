import { flushPromises, mount } from "@vue/test-utils";
import { QLayout, QPageContainer } from "quasar";
import { describe, expect, it, vi } from "vitest";
import AdminConversationsPage from "@/pages/admin/AdminConversationsPage.vue";
import { i18n } from "@/i18n";

vi.mock("@/api/admin", () => ({
  listConversations: vi.fn().mockResolvedValue([
    {
      id: 1,
      session_id: "demo-seed-session",
      language: "en",
      message_count: 2,
      latest_message_preview: "Tell me about Alex's platform engineering experience.",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ]),
  getConversationMessages: vi.fn().mockResolvedValue({ messages: [] }),
}));

describe("AdminConversationsPage", () => {
  it("renders seeded conversation preview", async () => {
    const wrapper = mount(
      {
        components: { QLayout, QPageContainer, AdminConversationsPage },
        template: "<q-layout><q-page-container><AdminConversationsPage /></q-page-container></q-layout>",
      },
      {
        global: { plugins: [i18n] },
      },
    );
    await flushPromises();

    expect(wrapper.text()).toContain("demo-seed-session");
    expect(wrapper.text()).toContain("platform engineering experience");
  });
});
