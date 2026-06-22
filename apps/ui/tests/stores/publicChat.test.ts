import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { usePublicChatStore } from "@/stores/publicChat";
import { usePublicSettingsStore } from "@/stores/publicSettings";

vi.mock("@/api/public", () => ({
  createPublicChatJob: vi.fn(),
  getPublicSettings: vi.fn(),
}));

vi.mock("@/api/chatJobs", () => ({
  pollPublicChatJob: vi.fn(),
}));

describe("public chat store", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("crypto", {
      randomUUID: () => `uuid-${Math.random().toString(36).slice(2, 8)}`,
    });
    setActivePinia(createPinia());
  });

  it("sends a message and appends assistant response", async () => {
    const { createPublicChatJob } = await import("@/api/public");
    const { pollPublicChatJob } = await import("@/api/chatJobs");

    vi.mocked(createPublicChatJob).mockResolvedValue({
      job_id: "job-1",
      conversation_id: 10,
      session_id: "session-1",
      status: "queued",
    });

    vi.mocked(pollPublicChatJob).mockResolvedValue({
      job_id: "job-1",
      conversation_id: 10,
      session_id: "session-1",
      status: "completed",
      response: {
        conversation_id: 10,
        session_id: "session-1",
        assistant_message: "Hello from assistant",
        language: "en",
        refused: false,
        grounded: true,
        sources: [{ source_type: "profile_item", title: "Leadership experience" }],
      },
      error_message: null,
    });

    const settingsStore = usePublicSettingsStore();
    settingsStore.selectedLanguage = "en";
    const store = usePublicChatStore();

    await store.sendMessage("Hello");

    expect(store.messages).toHaveLength(2);
    expect(store.messages[0]?.role).toBe("user");
    expect(store.messages[1]?.text).toBe("Hello from assistant");
    expect(store.messages[1]?.sources).toHaveLength(1);
    expect(store.conversationId).toBe(10);
    expect(createPublicChatJob).toHaveBeenCalledWith(
      expect.objectContaining({
        message: "Hello",
        language: "en",
      }),
    );
  });

  it("renders refused responses as assistant messages", async () => {
    const { createPublicChatJob } = await import("@/api/public");
    const { pollPublicChatJob } = await import("@/api/chatJobs");

    vi.mocked(createPublicChatJob).mockResolvedValue({
      job_id: "job-2",
      conversation_id: 11,
      session_id: "session-1",
      status: "processing",
    });

    vi.mocked(pollPublicChatJob).mockResolvedValue({
      job_id: "job-2",
      conversation_id: 11,
      session_id: "session-1",
      status: "completed",
      response: {
        conversation_id: 11,
        session_id: "session-1",
        assistant_message: "I cannot help with that request.",
        language: "en",
        refused: true,
        grounded: false,
        sources: [],
      },
      error_message: null,
    });

    const store = usePublicChatStore();
    await store.sendMessage("Sensitive request");

    expect(store.messages[1]?.refused).toBe(true);
    expect(store.messages[1]?.failed).toBeFalsy();
  });

  it("handles failed jobs as recoverable errors", async () => {
    const { createPublicChatJob } = await import("@/api/public");
    const { pollPublicChatJob } = await import("@/api/chatJobs");

    vi.mocked(createPublicChatJob).mockResolvedValue({
      job_id: "job-3",
      conversation_id: 12,
      session_id: "session-1",
      status: "queued",
    });

    vi.mocked(pollPublicChatJob).mockResolvedValue({
      job_id: "job-3",
      conversation_id: 12,
      session_id: "session-1",
      status: "failed",
      response: null,
      error_message: "Worker unavailable",
    });

    const store = usePublicChatStore();
    await store.sendMessage("Test");

    expect(store.messages[1]?.failed).toBe(true);
    expect(store.lastError).toBe("Worker unavailable");
  });
});
