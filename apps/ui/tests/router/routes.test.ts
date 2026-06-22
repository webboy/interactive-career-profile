import { describe, expect, it } from "vitest";
import router from "@/router";

describe("router", () => {
  it("registers public and admin routes", () => {
    const routeNames = router.getRoutes().map((route) => route.name);
    expect(routeNames).toContain("home");
    expect(routeNames).toContain("privacy");
    expect(routeNames).toContain("terms");
    expect(routeNames).toContain("admin-login");
    expect(routeNames).toContain("admin-home");
  });
});
