export function renderLegalMarkdown(content: string): string {
  const escaped = content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return escaped
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br />");
}

export function formatSourceType(sourceType: string): string {
  switch (sourceType) {
    case "profile_item":
      return "Profile";
    case "career_record":
      return "Career record";
    case "document_chunk":
      return "Document evidence";
    default:
      return sourceType.replace(/_/g, " ");
  }
}
