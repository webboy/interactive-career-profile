export type ChatJobPhase = "idle" | "submitting" | "queued" | "processing";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  refused?: boolean;
  grounded?: boolean;
  sources?: { source_type: string; title: string }[];
  failed?: boolean;
}

function createMessageId(): string {
  return crypto.randomUUID();
}

export function createUserMessage(text: string): ChatMessage {
  return {
    id: createMessageId(),
    role: "user",
    text,
  };
}

export function createAssistantMessage(
  text: string,
  options: {
    refused?: boolean;
    grounded?: boolean;
    sources?: { source_type: string; title: string }[];
    failed?: boolean;
  } = {},
): ChatMessage {
  return {
    id: createMessageId(),
    role: "assistant",
    text,
    refused: options.refused,
    grounded: options.grounded,
    sources: options.sources,
    failed: options.failed,
  };
}
