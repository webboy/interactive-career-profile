import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearStoredConversationId,
  getOrCreateSessionId,
  getStoredConversationId,
  getStoredLanguage,
  setStoredConversationId,
  setStoredLanguage,
} from "@/utils/session";

describe("session utils", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("crypto", {
      randomUUID: () => "session-test-uuid",
    });
  });

  it("creates and reuses session id", () => {
    expect(getOrCreateSessionId()).toBe("session-test-uuid");
    expect(getOrCreateSessionId()).toBe("session-test-uuid");
  });

  it("persists conversation id", () => {
    expect(getStoredConversationId()).toBeNull();
    setStoredConversationId(42);
    expect(getStoredConversationId()).toBe(42);
    clearStoredConversationId();
    expect(getStoredConversationId()).toBeNull();
  });

  it("persists selected language", () => {
    setStoredLanguage("de");
    expect(getStoredLanguage()).toBe("de");
  });
});
