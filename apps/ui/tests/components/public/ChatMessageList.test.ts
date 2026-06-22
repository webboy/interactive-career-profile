import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ChatMessageList from "@/components/public/ChatMessageList.vue";
import { i18n } from "@/i18n";

describe("ChatMessageList", () => {
  it("renders refused styling and source labels", () => {
    const wrapper = mount(ChatMessageList, {
      props: {
        messages: [
          {
            id: "1",
            role: "assistant",
            text: "Cannot answer that.",
            refused: true,
            sources: [{ source_type: "profile_item", title: "Profile summary" }],
          },
        ],
      },
      global: {
        plugins: [i18n],
      },
    });

    expect(wrapper.text()).toContain("Cannot answer that.");
    expect(wrapper.text()).toContain("Evidence (1)");
    expect(wrapper.text()).toContain("Profile summary");
  });
});
