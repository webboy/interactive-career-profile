import { createI18n } from "vue-i18n";
import en from "./en.json";
import de from "./de.json";
import sr from "./sr.json";

export const defaultLocale = "en";

export const i18n = createI18n({
  legacy: false,
  locale: defaultLocale,
  fallbackLocale: defaultLocale,
  messages: {
    en,
    de,
    sr,
  },
});

export type AppLocale = "en" | "de" | "sr";

export function setAppLocale(locale: string): void {
  if (locale in i18n.global.messages.value) {
    i18n.global.locale.value = locale as AppLocale;
  }
}
