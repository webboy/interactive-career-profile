import { apiRequest, getApiBaseUrl } from "./client";
import { ApiError } from "./types";
import type {
  AdminLegalPage,
  AdminSetting,
  CareerRecord,
  CareerRecordCreateRequest,
  CareerRecordUpdateRequest,
  ConversationListItem,
  ConversationMessagesResponse,
  DocumentChunk,
  DocumentIngestionActionResponse,
  DocumentRecord,
  DocumentTextCreateRequest,
  DocumentUpdateRequest,
  FollowUpRequest,
  JobSubmission,
  MeetingRequest,
  ProfileItem,
  ProfileItemCreateRequest,
  ProfileItemUpdateRequest,
  RetrievalLog,
  ToolCallsListResponse,
  UnansweredPrompt,
  Visibility,
} from "./adminTypes";

const ADMIN_OPTS = { credentials: "include" as RequestCredentials };

export async function apiFormRequest<T>(
  path: string,
  formData: FormData,
  method = "POST",
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    method,
    body: formData,
    credentials: ADMIN_OPTS.credentials,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      body && typeof body.detail === "string"
        ? body.detail
        : `Request failed with status ${response.status}`;
    throw new ApiError(detail, response.status, body);
  }

  return body as T;
}

// Settings
export function listAdminSettings(): Promise<AdminSetting[]> {
  return apiRequest<AdminSetting[]>("/api/admin/settings", {}, ADMIN_OPTS);
}

export function updateAdminSetting(key: string, value: string, isSecret = false): Promise<AdminSetting> {
  return apiRequest<AdminSetting>(
    `/api/admin/settings/${encodeURIComponent(key)}`,
    { method: "PUT", body: JSON.stringify({ value, is_secret: isSecret }) },
    ADMIN_OPTS,
  );
}

// Legal
export function getAdminLegalPage(slug: string): Promise<AdminLegalPage> {
  return apiRequest<AdminLegalPage>(`/api/admin/legal-pages/${slug}`, {}, ADMIN_OPTS);
}

export function updateAdminLegalPage(
  slug: string,
  title: string,
  content: string,
): Promise<AdminLegalPage> {
  return apiRequest<AdminLegalPage>(
    `/api/admin/legal-pages/${slug}`,
    { method: "PUT", body: JSON.stringify({ title, content }) },
    ADMIN_OPTS,
  );
}

// Profile items
export function listProfileItems(visibility?: Visibility): Promise<ProfileItem[]> {
  const params = visibility ? `?visibility=${visibility}` : "";
  return apiRequest<ProfileItem[]>(`/api/admin/profile-items${params}`, {}, ADMIN_OPTS);
}

export function createProfileItem(payload: ProfileItemCreateRequest): Promise<ProfileItem> {
  return apiRequest<ProfileItem>(
    "/api/admin/profile-items",
    { method: "POST", body: JSON.stringify(payload) },
    ADMIN_OPTS,
  );
}

export function updateProfileItem(id: number, payload: ProfileItemUpdateRequest): Promise<ProfileItem> {
  return apiRequest<ProfileItem>(
    `/api/admin/profile-items/${id}`,
    { method: "PUT", body: JSON.stringify(payload) },
    ADMIN_OPTS,
  );
}

export function deleteProfileItem(id: number): Promise<void> {
  return apiRequest<void>(`/api/admin/profile-items/${id}`, { method: "DELETE" }, ADMIN_OPTS);
}

// Career records
export function listCareerRecords(params?: {
  visibility?: Visibility;
  record_type?: string;
}): Promise<CareerRecord[]> {
  const search = new URLSearchParams();
  if (params?.visibility) search.set("visibility", params.visibility);
  if (params?.record_type) search.set("record_type", params.record_type);
  const qs = search.toString();
  return apiRequest<CareerRecord[]>(`/api/admin/career-records${qs ? `?${qs}` : ""}`, {}, ADMIN_OPTS);
}

export function createCareerRecord(payload: CareerRecordCreateRequest): Promise<CareerRecord> {
  return apiRequest<CareerRecord>(
    "/api/admin/career-records",
    { method: "POST", body: JSON.stringify(payload) },
    ADMIN_OPTS,
  );
}

export function updateCareerRecord(id: number, payload: CareerRecordUpdateRequest): Promise<CareerRecord> {
  return apiRequest<CareerRecord>(
    `/api/admin/career-records/${id}`,
    { method: "PUT", body: JSON.stringify(payload) },
    ADMIN_OPTS,
  );
}

export function deleteCareerRecord(id: number): Promise<void> {
  return apiRequest<void>(`/api/admin/career-records/${id}`, { method: "DELETE" }, ADMIN_OPTS);
}

// Documents
export function listDocuments(params?: { visibility?: Visibility; status?: string }): Promise<DocumentRecord[]> {
  const search = new URLSearchParams();
  if (params?.visibility) search.set("visibility", params.visibility);
  if (params?.status) search.set("status", params.status);
  const qs = search.toString();
  return apiRequest<DocumentRecord[]>(`/api/admin/documents${qs ? `?${qs}` : ""}`, {}, ADMIN_OPTS);
}

export function getDocument(id: number): Promise<DocumentRecord> {
  return apiRequest<DocumentRecord>(`/api/admin/documents/${id}`, {}, ADMIN_OPTS);
}

export function uploadDocument(file: File, title?: string, visibility: Visibility = "draft"): Promise<DocumentRecord> {
  const form = new FormData();
  form.append("file", file);
  if (title) form.append("title", title);
  form.append("visibility", visibility);
  return apiFormRequest<DocumentRecord>("/api/admin/documents/upload", form);
}

export function createTextDocument(payload: DocumentTextCreateRequest): Promise<DocumentRecord> {
  return apiRequest<DocumentRecord>(
    "/api/admin/documents/text",
    { method: "POST", body: JSON.stringify(payload) },
    ADMIN_OPTS,
  );
}

export function updateDocument(id: number, payload: DocumentUpdateRequest): Promise<DocumentRecord> {
  return apiRequest<DocumentRecord>(
    `/api/admin/documents/${id}`,
    { method: "PUT", body: JSON.stringify(payload) },
    ADMIN_OPTS,
  );
}

export function deleteDocument(id: number): Promise<void> {
  return apiRequest<void>(`/api/admin/documents/${id}`, { method: "DELETE" }, ADMIN_OPTS);
}

export function extractDocument(id: number): Promise<DocumentIngestionActionResponse> {
  return apiRequest<DocumentIngestionActionResponse>(
    `/api/admin/documents/${id}/extract`,
    { method: "POST" },
    ADMIN_OPTS,
  );
}

export function chunkDocument(id: number): Promise<DocumentIngestionActionResponse> {
  return apiRequest<DocumentIngestionActionResponse>(
    `/api/admin/documents/${id}/chunk`,
    { method: "POST" },
    ADMIN_OPTS,
  );
}

export function retryDocumentIngestion(id: number): Promise<DocumentIngestionActionResponse> {
  return apiRequest<DocumentIngestionActionResponse>(
    `/api/admin/documents/${id}/retry-ingestion`,
    { method: "POST" },
    ADMIN_OPTS,
  );
}

export function requestDocumentEmbedding(id: number): Promise<DocumentRecord> {
  return apiRequest<DocumentRecord>(
    `/api/admin/documents/${id}/request-embedding`,
    { method: "POST" },
    ADMIN_OPTS,
  );
}

export function listDocumentChunks(documentId: number): Promise<DocumentChunk[]> {
  return apiRequest<DocumentChunk[]>(`/api/admin/documents/${documentId}/chunks`, {}, ADMIN_OPTS);
}

export function updateDocumentChunkVisibility(chunkId: number, visibility: Visibility): Promise<DocumentChunk> {
  return apiRequest<DocumentChunk>(
    `/api/admin/document-chunks/${chunkId}`,
    { method: "PUT", body: JSON.stringify({ visibility }) },
    ADMIN_OPTS,
  );
}

export function embedDocumentChunk(chunkId: number): Promise<{ chunk_id: number; embedding_status: string }> {
  return apiRequest(
    `/api/admin/document-chunks/${chunkId}/embed`,
    { method: "POST" },
    ADMIN_OPTS,
  );
}

// Retrieval & observability
export function listRetrievalLogs(limit = 50): Promise<RetrievalLog[]> {
  return apiRequest<RetrievalLog[]>(`/api/admin/retrieval-logs?limit=${limit}`, {}, ADMIN_OPTS);
}

export function getRetrievalLog(id: number): Promise<RetrievalLog> {
  return apiRequest<RetrievalLog>(`/api/admin/retrieval-logs/${id}`, {}, ADMIN_OPTS);
}

export function listUnansweredPrompts(limit = 50): Promise<UnansweredPrompt[]> {
  return apiRequest<UnansweredPrompt[]>(`/api/admin/unanswered-prompts?limit=${limit}`, {}, ADMIN_OPTS);
}

export function listConversations(limit = 50): Promise<ConversationListItem[]> {
  return apiRequest<ConversationListItem[]>(`/api/admin/conversations?limit=${limit}`, {}, ADMIN_OPTS);
}

export function getConversationMessages(conversationId: number): Promise<ConversationMessagesResponse> {
  return apiRequest<ConversationMessagesResponse>(
    `/api/admin/conversations/${conversationId}/messages`,
    {},
    ADMIN_OPTS,
  );
}

// Leads
export function listMeetingRequests(): Promise<MeetingRequest[]> {
  return apiRequest<MeetingRequest[]>("/api/admin/leads/meeting-requests", {}, ADMIN_OPTS);
}

export function listFollowUpRequests(): Promise<FollowUpRequest[]> {
  return apiRequest<FollowUpRequest[]>("/api/admin/leads/follow-up-requests", {}, ADMIN_OPTS);
}

export function listJobSubmissions(): Promise<JobSubmission[]> {
  return apiRequest<JobSubmission[]>("/api/admin/leads/job-submissions", {}, ADMIN_OPTS);
}

export function listToolCalls(): Promise<ToolCallsListResponse> {
  return apiRequest<ToolCallsListResponse>("/api/admin/tool-calls", {}, ADMIN_OPTS);
}
