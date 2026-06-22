import { flushPromises, mount } from "@vue/test-utils";
import { QLayout, QPageContainer } from "quasar";
import { describe, expect, it, vi } from "vitest";
import AdminLeadsPage from "@/pages/admin/AdminLeadsPage.vue";
import { i18n } from "@/i18n";

vi.mock("@/api/admin", () => ({
  listMeetingRequests: vi.fn().mockResolvedValue([
    {
      id: 1,
      status: "new",
      admin_email_status: "sent",
      requester_email_status: "sent",
      requester_name: "Alex",
      requester_email: "alex@example.com",
      organization: "ACME",
      message: "Let's meet",
      preferred_times: "Next week",
    },
  ]),
  listFollowUpRequests: vi.fn().mockResolvedValue([]),
  listJobSubmissions: vi.fn().mockResolvedValue([]),
}));

describe("AdminLeadsPage", () => {
  it("renders meeting requests", async () => {
    const wrapper = mount(
      {
        components: { QLayout, QPageContainer, AdminLeadsPage },
        template: "<q-layout><q-page-container><AdminLeadsPage /></q-page-container></q-layout>",
      },
      {
        global: { plugins: [i18n] },
      },
    );
    await flushPromises();
    expect(wrapper.text()).toContain("Alex");
    expect(wrapper.text()).toContain("Let's meet");
  });
});
