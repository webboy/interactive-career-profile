import { flushPromises, mount } from "@vue/test-utils";
import { QLayout, QPageContainer } from "quasar";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PublicLayout from "@/layouts/PublicLayout.vue";
import { i18n } from "@/i18n";
import { createPinia, setActivePinia } from "pinia";
import { usePublicSettingsStore } from "@/stores/publicSettings";

const push = vi.fn();

vi.mock("vue-router", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/api/public", () => ({
  getPublicSettings: vi.fn().mockResolvedValue({
    app_name: "ICP Demo",
    app_url: "http://localhost:9000",
    default_language: "en",
    supported_languages: ["en", "de", "sr"],
  }),
}));

describe("PublicLayout language dropdown", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders supported languages and persists selection", async () => {
    const settingsStore = usePublicSettingsStore();
    await settingsStore.loadSettings();

    const wrapper = mount(
      {
        components: { QLayout, QPageContainer, PublicLayout },
        template: "<PublicLayout><div>content</div></PublicLayout>",
      },
      {
        global: {
          plugins: [i18n],
          stubs: { "router-view": true },
        },
      },
    );
    await flushPromises();

    expect(wrapper.text()).toContain("ICP Demo");
    expect(wrapper.text()).toContain("EN");

    settingsStore.setLanguage("de");
    expect(settingsStore.selectedLanguage).toBe("de");
  });
});
