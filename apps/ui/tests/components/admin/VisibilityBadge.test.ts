import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import VisibilityBadge from "@/components/admin/VisibilityBadge.vue";

describe("VisibilityBadge", () => {
  it("renders visibility label", () => {
    const wrapper = mount(VisibilityBadge, {
      props: { visibility: "public" },
    });
    expect(wrapper.text()).toContain("public");
  });
});
