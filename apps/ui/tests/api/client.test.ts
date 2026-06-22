import { describe, expect, it, vi } from "vitest";
import { apiRequest, getApiBaseUrl } from "@/api/client";
import { ApiError } from "@/api/types";

describe("api client", () => {
  it("uses configured API base URL", () => {
    expect(getApiBaseUrl()).toBe("");
  });

  it("throws ApiError with normalized message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        headers: { get: () => "application/json" },
        json: async () => ({ detail: "Conversation does not belong to session" }),
      }),
    );

    await expect(apiRequest("/api/public/chat")).rejects.toMatchObject({
      status: 400,
      message: "Conversation does not belong to session",
    } satisfies Partial<ApiError>);

    vi.unstubAllGlobals();
  });
});
