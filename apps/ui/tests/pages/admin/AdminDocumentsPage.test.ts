import { flushPromises, mount } from "@vue/test-utils";
import { QLayout, QPageContainer } from "quasar";
import { describe, expect, it, vi } from "vitest";
import AdminDocumentsPage from "@/pages/admin/AdminDocumentsPage.vue";
import { i18n } from "@/i18n";

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/api/admin", () => ({
  listDocuments: vi.fn().mockResolvedValue([
    {
      id: 1,
      title: "Demo: Platform Migration Case Study",
      visibility: "public",
      status: "chunked",
      source_type: "pasted_text",
      embedding_status: "ready",
    },
    {
      id: 2,
      title: "Demo: Private Interview Notes",
      visibility: "private",
      status: "chunked",
      source_type: "pasted_text",
      embedding_status: "ready",
    },
  ]),
  createTextDocument: vi.fn(),
  deleteDocument: vi.fn(),
  uploadDocument: vi.fn(),
}));

describe("AdminDocumentsPage", () => {
  it("renders seeded demo documents", async () => {
    const wrapper = mount(
      {
        components: { QLayout, QPageContainer, AdminDocumentsPage },
        template: "<q-layout><q-page-container><AdminDocumentsPage /></q-page-container></q-layout>",
      },
      {
        global: { plugins: [i18n] },
      },
    );
    await flushPromises();

    expect(wrapper.text()).toContain("Demo: Platform Migration Case Study");
    expect(wrapper.text()).toContain("Demo: Private Interview Notes");
  });
});
