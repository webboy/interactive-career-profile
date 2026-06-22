import { defineStore } from "pinia";
import { getPublicSettings } from "@/api/public";
import type { PublicSettingsResponse } from "@/api/types";
import { setAppLocale } from "@/i18n";

export const usePublicSettingsStore = defineStore("publicSettings", {
  state: () => ({
    settings: null as PublicSettingsResponse | null,
    loading: false,
    error: null as string | null,
    selectedLanguage: "en",
  }),
  getters: {
    appName: (state) => state.settings?.app_name ?? "Interactive Career Profile",
    supportedLanguages: (state) => state.settings?.supported_languages ?? ["en"],
  },
  actions: {
    async loadSettings(force = false): Promise<PublicSettingsResponse | null> {
      if (this.settings && !force) {
        return this.settings;
      }
      this.loading = true;
      this.error = null;
      try {
        this.settings = await getPublicSettings();
        this.selectedLanguage = this.settings.default_language;
        setAppLocale(this.selectedLanguage);
        return this.settings;
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load settings";
        return null;
      } finally {
        this.loading = false;
      }
    },
    setLanguage(language: string): void {
      this.selectedLanguage = language;
      setAppLocale(language);
    },
  },
});
