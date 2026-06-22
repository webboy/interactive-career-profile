import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import LeadPromptCards from "@/components/public/LeadPromptCards.vue";
import { i18n } from "@/i18n";

describe("LeadPromptCards", () => {
  it("emits guided prompt text", async () => {
    const wrapper = mount(LeadPromptCards, {
      global: {
        plugins: [i18n],
      },
    });

    await wrapper.findAll("button")[0]?.trigger("click");

    expect(wrapper.emitted("select")?.[0]?.[0]).toContain("schedule a meeting");
  });
});
