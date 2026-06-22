import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import LegalPageView from "@/components/public/LegalPageView.vue";
import { i18n } from "@/i18n";

describe("LegalPageView", () => {
  it("renders loading and markdown content states", async () => {
    const fetchPage = () =>
      Promise.resolve({
        slug: "privacy",
        title: "Privacy Policy",
        content: "# Privacy\n\n**Important** notice",
        updated_at: "2026-01-01T00:00:00Z",
      });

    const wrapper = mount(LegalPageView, {
      props: { fetchPage },
      global: {
        plugins: [i18n],
      },
    });

    expect(wrapper.text()).toContain("Loading legal page");

    await flushPromises();

    expect(wrapper.text()).toContain("Privacy Policy");
    expect(wrapper.find(".legal-content").html()).toContain("<strong>Important</strong>");
  });
});
