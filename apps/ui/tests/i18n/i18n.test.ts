import { describe, expect, it } from "vitest";
import { i18n, setAppLocale } from "@/i18n";

describe("i18n", () => {
  it("switches locale for supported languages", () => {
    setAppLocale("de");
    expect(i18n.global.locale.value).toBe("de");
    expect(i18n.global.t("app.title")).toContain("Karriereprofil");
  });
});
