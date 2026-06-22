import { defineStore } from "pinia";
import { createPublicChatJob } from "@/api/public";
import { pollPublicChatJob } from "@/api/chatJobs";
import { ApiError } from "@/api/types";
import { usePublicSettingsStore } from "@/stores/publicSettings";
import {
  createAssistantMessage,
  createUserMessage,
  type ChatJobPhase,
  type ChatMessage,
} from "@/stores/publicChatTypes";
import {
  clearStoredConversationId,
  getOrCreateSessionId,
  getStoredConversationId,
  setStoredConversationId,
} from "@/utils/session";

export const usePublicChatStore = defineStore("publicChat", {
  state: () => ({
    sessionId: getOrCreateSessionId(),
    conversationId: getStoredConversationId() as number | null,
    messages: [] as ChatMessage[],
    jobPhase: "idle" as ChatJobPhase,
    lastError: null as string | null,
    abortController: null as AbortController | null,
  }),
  getters: {
    isBusy: (state) => state.jobPhase !== "idle",
  },
  actions: {
    resetConversationMismatch(): void {
      this.conversationId = null;
      clearStoredConversationId();
    },
    async sendMessage(text: string): Promise<void> {
      const trimmed = text.trim();
      if (!trimmed || this.jobPhase !== "idle") {
        return;
      }

      const settingsStore = usePublicSettingsStore();
      this.lastError = null;
      this.messages.push(createUserMessage(trimmed));
      this.jobPhase = "submitting";
      this.abortController?.abort();
      this.abortController = new AbortController();
      const signal = this.abortController.signal;

      try {
        const created = await createPublicChatJob({
          message: trimmed,
          session_id: this.sessionId,
          conversation_id: this.conversationId ?? undefined,
          language: settingsStore.selectedLanguage,
        });

        this.conversationId = created.conversation_id;
        setStoredConversationId(created.conversation_id);
        this.jobPhase = created.status === "processing" ? "processing" : "queued";

        const result = await pollPublicChatJob(created.job_id, this.sessionId, {
          intervalMs: 500,
          maxAttempts: 120,
          signal,
          onStatusChange: (status) => {
            this.setJobPhaseFromPoll(status.status);
          },
        });

        if (result.status === "failed") {
          this.messages.push(
            createAssistantMessage(
              result.error_message ||
                "The chat response could not be prepared. Please try again.",
              { failed: true },
            ),
          );
          this.lastError =
            result.error_message ||
            "The chat response could not be prepared. Please try again.";
          return;
        }

        const response = result.response;
        if (!response) {
          throw new Error("Completed job did not include a response");
        }

        this.conversationId = response.conversation_id;
        setStoredConversationId(response.conversation_id);
        this.messages.push(
          createAssistantMessage(response.assistant_message, {
            refused: response.refused,
            grounded: response.grounded,
            sources: response.sources,
          }),
        );
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        if (error instanceof ApiError && error.status === 400) {
          this.resetConversationMismatch();
        }
        const message =
          error instanceof Error ? error.message : "Something went wrong while sending your message.";
        this.lastError = message;
        this.messages.push(createAssistantMessage(message, { failed: true }));
      } finally {
        this.jobPhase = "idle";
        this.abortController = null;
      }
    },
    setJobPhaseFromPoll(status: string): void {
      if (status === "queued") {
        this.jobPhase = "queued";
      } else if (status === "processing") {
        this.jobPhase = "processing";
      }
    },
  },
});
