import { defineStore } from "pinia";
import { getPublicSettings } from "@/api/public";
import type { PublicSettingsResponse } from "@/api/types";
import { setAppLocale } from "@/i18n";
import { getStoredLanguage, setStoredLanguage } from "@/utils/session";

export const usePublicSettingsStore = defineStore("publicSettings", {
  state: () => ({
    settings: null as PublicSettingsResponse | null,
    loading: false,
    error: null as string | null,
    selectedLanguage: getStoredLanguage() ?? "en",
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
        const storedLanguage = getStoredLanguage();
        const defaultLanguage = this.settings.default_language;
        const supported = this.settings.supported_languages;
        const nextLanguage =
          storedLanguage && supported.includes(storedLanguage)
            ? storedLanguage
            : defaultLanguage;
        this.selectedLanguage = nextLanguage;
        setAppLocale(nextLanguage);
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
      setStoredLanguage(language);
      setAppLocale(language);
    },
  },
});
