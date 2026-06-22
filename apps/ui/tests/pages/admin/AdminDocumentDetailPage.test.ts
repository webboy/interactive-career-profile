import { flushPromises, mount } from "@vue/test-utils";
import { QLayout, QPageContainer } from "quasar";
import { describe, expect, it, vi } from "vitest";
import AdminDocumentDetailPage from "@/pages/admin/AdminDocumentDetailPage.vue";
import { i18n } from "@/i18n";

vi.mock("vue-router", () => ({
  useRoute: () => ({ params: { id: "1" } }),
}));

vi.mock("@/api/admin", () => ({
  getDocument: vi.fn().mockResolvedValue({
    id: 1,
    title: "Demo: Platform Migration Case Study",
    visibility: "public",
    status: "chunked",
    source_type: "pasted_text",
    embedding_status: "ready",
  }),
  listDocumentChunks: vi.fn().mockResolvedValue([
    {
      id: 1,
      document_id: 1,
      chunk_index: 0,
      content: "Alex Rivera led a multi-region platform migration.",
      visibility: "public",
      embedding_status: "ready",
    },
  ]),
  updateDocument: vi.fn(),
  extractDocument: vi.fn(),
  chunkDocument: vi.fn(),
  requestDocumentEmbedding: vi.fn(),
  retryDocumentIngestion: vi.fn(),
  embedDocumentChunk: vi.fn(),
  updateDocumentChunkVisibility: vi.fn().mockResolvedValue({
    id: 1,
    visibility: "private",
  }),
}));

describe("AdminDocumentDetailPage", () => {
  it("renders chunk visibility controls and wires update action", async () => {
    const { updateDocumentChunkVisibility } = await import("@/api/admin");

    const wrapper = mount(
      {
        components: { QLayout, QPageContainer, AdminDocumentDetailPage },
        template: "<q-layout><q-page-container><AdminDocumentDetailPage /></q-page-container></q-layout>",
      },
      {
        global: { plugins: [i18n] },
      },
    );
    await flushPromises();

    expect(wrapper.text()).toContain("Demo: Platform Migration Case Study");
    expect(wrapper.text()).toContain("platform migration");

    const selects = wrapper.findAllComponents({ name: "QSelect" });
    expect(selects.length).toBeGreaterThan(1);
    await selects[1]?.vm.$emit("update:model-value", "private");
    await flushPromises();

    expect(updateDocumentChunkVisibility).toHaveBeenCalled();
  });
});
