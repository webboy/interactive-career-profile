import { apiRequest } from "./client";
import type {
  LegalPageResponse,
  PublicChatJobCreateResponse,
  PublicChatJobStatusResponse,
  PublicChatRequest,
  PublicSettingsResponse,
} from "./types";

export function getPublicSettings(): Promise<PublicSettingsResponse> {
  return apiRequest<PublicSettingsResponse>("/api/public/settings");
}

export function getPrivacyPage(): Promise<LegalPageResponse> {
  return apiRequest<LegalPageResponse>("/api/public/privacy");
}

export function getTermsPage(): Promise<LegalPageResponse> {
  return apiRequest<LegalPageResponse>("/api/public/terms");
}

export function createPublicChatJob(
  body: PublicChatRequest,
): Promise<PublicChatJobCreateResponse> {
  return apiRequest<PublicChatJobCreateResponse>("/api/public/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getPublicChatJob(
  jobId: string,
  sessionId: string,
): Promise<PublicChatJobStatusResponse> {
  const params = new URLSearchParams({ session_id: sessionId });
  return apiRequest<PublicChatJobStatusResponse>(
    `/api/public/chat/jobs/${encodeURIComponent(jobId)}?${params.toString()}`,
  );
}
