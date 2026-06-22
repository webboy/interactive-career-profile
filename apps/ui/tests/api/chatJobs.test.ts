import { describe, expect, it, vi } from "vitest";
import { pollPublicChatJob } from "@/api/chatJobs";
import * as publicApi from "@/api/public";

describe("chat job polling", () => {
  it("polls until completed", async () => {
    const getJobSpy = vi.spyOn(publicApi, "getPublicChatJob");
    getJobSpy
      .mockResolvedValueOnce({
        job_id: "job-1",
        conversation_id: 1,
        session_id: "session-1",
        status: "processing",
        response: null,
        error_message: null,
      })
      .mockResolvedValueOnce({
        job_id: "job-1",
        conversation_id: 1,
        session_id: "session-1",
        status: "completed",
        response: {
          conversation_id: 1,
          session_id: "session-1",
          assistant_message: "Hello",
          language: "en",
          refused: false,
          grounded: true,
          sources: [],
        },
        error_message: null,
      });

    const result = await pollPublicChatJob("job-1", "session-1", {
      intervalMs: 1,
      maxAttempts: 5,
    });

    expect(result.status).toBe("completed");
    expect(result.response?.assistant_message).toBe("Hello");
    expect(getJobSpy).toHaveBeenCalledTimes(2);

    getJobSpy.mockRestore();
  });
});
