import { describe, expect, it } from "vitest";
import { formatSourceType, renderLegalMarkdown } from "@/utils/format";

describe("format utils", () => {
  it("renders basic legal markdown", () => {
    const html = renderLegalMarkdown("# Title\n\n**Bold** line");
    expect(html).toContain("<h1>Title</h1>");
    expect(html).toContain("<strong>Bold</strong>");
  });

  it("formats known source types", () => {
    expect(formatSourceType("profile_item")).toBe("Profile");
    expect(formatSourceType("document_chunk")).toBe("Document evidence");
  });
});
