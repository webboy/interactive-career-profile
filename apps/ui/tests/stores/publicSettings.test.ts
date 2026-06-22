import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { usePublicSettingsStore } from "@/stores/publicSettings";

vi.mock("@/api/public", () => ({
  getPublicSettings: vi.fn(),
}));

describe("public settings store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("loads settings and applies default language", async () => {
    const { getPublicSettings } = await import("@/api/public");
    vi.mocked(getPublicSettings).mockResolvedValue({
      app_name: "ICP",
      app_url: "http://localhost:9000",
      default_language: "de",
      supported_languages: ["en", "de", "sr"],
    });

    const store = usePublicSettingsStore();
    await store.loadSettings();

    expect(store.appName).toBe("ICP");
    expect(store.selectedLanguage).toBe("de");
    expect(store.supportedLanguages).toEqual(["en", "de", "sr"]);
  });
});
