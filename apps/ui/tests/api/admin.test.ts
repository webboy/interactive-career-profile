import { describe, expect, it, vi } from "vitest";
import * as client from "@/api/client";
import { listProfileItems, listConversations, updateAdminSetting } from "@/api/admin";

describe("admin api client", () => {
  it("loads profile items with credentials", async () => {
    const spy = vi.spyOn(client, "apiRequest").mockResolvedValue([]);
    await listProfileItems();
    expect(spy).toHaveBeenCalledWith("/api/admin/profile-items", {}, { credentials: "include" });
    spy.mockRestore();
  });

  it("updates settings with PUT payload", async () => {
    const spy = vi.spyOn(client, "apiRequest").mockResolvedValue({
      key: "app_name",
      value: "ICP",
      is_secret: false,
    });
    await updateAdminSetting("app_name", "ICP");
    expect(spy).toHaveBeenCalledWith(
      "/api/admin/settings/app_name",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ value: "ICP", is_secret: false }),
      }),
      { credentials: "include" },
    );
    spy.mockRestore();
  });

  it("loads conversations list", async () => {
    const spy = vi.spyOn(client, "apiRequest").mockResolvedValue([]);
    await listConversations(25);
    expect(spy).toHaveBeenCalledWith("/api/admin/conversations?limit=25", {}, { credentials: "include" });
    spy.mockRestore();
  });
});
