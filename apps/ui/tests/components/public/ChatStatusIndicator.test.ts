import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import ChatStatusIndicator from "@/components/public/ChatStatusIndicator.vue";
import { i18n } from "@/i18n";

describe("ChatStatusIndicator", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("shows queued and processing states", () => {
    const queued = mount(ChatStatusIndicator, {
      props: { phase: "queued" },
      global: { plugins: [i18n] },
    });
    expect(queued.text()).toContain("queued");

    const processing = mount(ChatStatusIndicator, {
      props: { phase: "processing" },
      global: { plugins: [i18n] },
    });
    expect(processing.text()).toContain("Preparing a response");
  });

  it("hides when idle", () => {
    const wrapper = mount(ChatStatusIndicator, {
      props: { phase: "idle" },
      global: { plugins: [i18n] },
    });
    expect(wrapper.text()).toBe("");
  });
});
