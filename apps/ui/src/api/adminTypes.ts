export type Visibility = "public" | "private" | "draft" | "archived";
export type ProfileItemType =
  | "text"
  | "link"
  | "email"
  | "location"
  | "language"
  | "availability"
  | "other";
export type CareerRecordType =
  | "experience"
  | "project"
  | "skill"
  | "education"
  | "certification"
  | "language"
  | "achievement"
  | "leadership"
  | "availability"
  | "other";
export type EmbeddingStatus = "pending" | "ready" | "failed" | "not_required";
export type DocumentSourceType = "upload" | "pasted_text";
export type DocumentStatus = "uploaded" | "extracted" | "chunked" | "failed";
export type DocumentFileType = "pdf" | "docx" | "txt" | "markdown" | "text";
export type SourceCategory = "profile_item" | "career_record" | "document_chunk";
export type UnansweredPromptReason =
  | "no_context"
  | "below_threshold"
  | "policy"
  | "other";

export interface AdminSetting {
  key: string;
  value: string;
  is_secret: boolean;
}

export interface AdminLegalPage {
  slug: string;
  title: string;
  content: string;
  updated_at: string;
}

export interface ProfileItem {
  id: number;
  key: string;
  type: ProfileItemType;
  label: string;
  value: string;
  visibility: Visibility;
  source: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProfileItemCreateRequest {
  key: string;
  type: ProfileItemType;
  label: string;
  value: string;
  visibility?: Visibility;
  source?: string | null;
  sort_order?: number;
}

export interface ProfileItemUpdateRequest extends ProfileItemCreateRequest {
  visibility: Visibility;
}

export interface CareerRecord {
  id: number;
  record_type: CareerRecordType;
  title: string;
  summary: string | null;
  content: string;
  visibility: Visibility;
  source: string | null;
  tags: string | null;
  start_date: string | null;
  end_date: string | null;
  sort_order: number;
  embedding_status: EmbeddingStatus;
  embedding_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface CareerRecordCreateRequest {
  record_type: CareerRecordType;
  title: string;
  summary?: string | null;
  content: string;
  visibility?: Visibility;
  source?: string | null;
  tags?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  sort_order?: number;
  embedding_status?: EmbeddingStatus;
}

export interface CareerRecordUpdateRequest extends CareerRecordCreateRequest {
  visibility: Visibility;
  embedding_status: EmbeddingStatus;
  embedding_error?: string | null;
}

export interface DocumentRecord {
  id: number;
  title: string;
  source_type: DocumentSourceType;
  file_type: DocumentFileType | null;
  original_filename: string | null;
  storage_path: string | null;
  mime_type: string | null;
  file_size_bytes: number | null;
  extracted_text: string | null;
  visibility: Visibility;
  status: DocumentStatus;
  status_error: string | null;
  embedding_status: EmbeddingStatus;
  embedding_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentTextCreateRequest {
  title: string;
  content: string;
  visibility?: Visibility;
}

export interface DocumentUpdateRequest {
  title: string;
  visibility: Visibility;
}

export interface DocumentChunk {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  char_start: number;
  char_end: number;
  visibility: Visibility;
  embedding_status: EmbeddingStatus;
  embedding_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentIngestionActionResponse {
  document: DocumentRecord;
  chunks_created?: number | null;
}

export interface RetrievalLogItem {
  id: number;
  source_type: SourceCategory;
  source_id: number;
  title: string;
  snippet: string;
  score: number | null;
  visibility: Visibility;
  was_used: boolean;
  precedence_rank: number;
}

export interface RetrievalLog {
  id: number;
  query: string;
  language: string | null;
  session_id: string | null;
  structured_limit: number;
  document_limit: number;
  document_score_threshold: number;
  had_usable_context: boolean;
  created_at: string;
  items: RetrievalLogItem[];
}

export interface UnansweredPrompt {
  id: number;
  query: string;
  reason: UnansweredPromptReason;
  language: string | null;
  session_id: string | null;
  retrieval_log_id: number | null;
  created_at: string;
}

export interface ConversationListItem {
  id: number;
  session_id: string | null;
  language: string | null;
  message_count: number;
  latest_message_preview: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: number;
  role: string;
  content: string;
}

export interface ConversationMessagesResponse {
  conversation_id: number;
  messages: ConversationMessage[];
}

export interface LeadRecordBase {
  id: number;
  status: string;
  admin_email_status: string;
  requester_email_status: string;
}

export interface MeetingRequest extends LeadRecordBase {
  requester_name: string;
  requester_email: string;
  organization: string | null;
  message: string | null;
  preferred_times: string | null;
}

export interface FollowUpRequest extends LeadRecordBase {
  requester_email: string;
  question: string;
}

export interface JobSubmission extends LeadRecordBase {
  requester_email: string;
  company: string | null;
  role_title: string | null;
  job_description: string;
  role_fit_summary: string | null;
  retrieval_log_id: number | null;
}

export interface ToolCallRecord {
  id: number;
  conversation_id: number;
  tool_name: string;
  status: string;
  request_payload: string | null;
  response_payload: string | null;
  error_message: string | null;
}

export interface ToolCallsListResponse {
  tool_calls: ToolCallRecord[];
}
