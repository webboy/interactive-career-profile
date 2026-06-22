import { flushPromises, mount } from "@vue/test-utils";
import { QLayout, QPageContainer } from "quasar";
import { describe, expect, it, vi } from "vitest";
import AdminRetrievalLogsPage from "@/pages/admin/AdminRetrievalLogsPage.vue";
import { i18n } from "@/i18n";

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/api/admin", () => ({
  listRetrievalLogs: vi.fn().mockResolvedValue([
    {
      id: 10,
      query: "Where is Alex Rivera based as Senior Platform Engineer?",
      language: "en",
      session_id: "demo-seed-session",
      had_usable_context: true,
      created_at: "2026-01-01T00:00:00Z",
    },
  ]),
  listUnansweredPrompts: vi.fn().mockResolvedValue([
    {
      id: 1,
      query: "zzzz-nonexistent-quantum-chemistry-topic-demo",
      reason: "no_context",
      language: "en",
      session_id: "demo-seed-session",
      retrieval_log_id: 11,
      created_at: "2026-01-01T00:00:00Z",
    },
  ]),
  getRetrievalLog: vi.fn(),
}));

describe("AdminRetrievalLogsPage", () => {
  it("renders seeded retrieval logs", async () => {
    const wrapper = mount(
      {
        components: { QLayout, QPageContainer, AdminRetrievalLogsPage },
        template: "<q-layout><q-page-container><AdminRetrievalLogsPage /></q-page-container></q-layout>",
      },
      {
        global: { plugins: [i18n] },
      },
    );
    await flushPromises();

    expect(wrapper.text()).toContain("Alex Rivera");
    expect(wrapper.text()).toContain("quantum-chemistry-topic-demo");
  });
});
