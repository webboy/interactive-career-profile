export type ChatJobStatus = "queued" | "processing" | "completed" | "failed";

export interface PublicSettingsResponse {
  app_name: string;
  app_url: string;
  default_language: string;
  supported_languages: string[];
}

export interface PublicChatRequest {
  message: string;
  session_id: string;
  conversation_id?: number;
  language?: string;
}

export interface PublicSourceSummary {
  source_type: string;
  title: string;
}

export interface PublicChatResponse {
  conversation_id: number;
  session_id: string;
  assistant_message: string;
  language: string;
  refused: boolean;
  grounded: boolean;
  sources: PublicSourceSummary[];
}

export interface PublicChatJobCreateResponse {
  job_id: string;
  conversation_id: number;
  session_id: string;
  status: ChatJobStatus;
}

export interface PublicChatJobStatusResponse {
  job_id: string;
  conversation_id: number;
  session_id: string;
  status: ChatJobStatus;
  response: PublicChatResponse | null;
  error_message: string | null;
}

export interface LegalPageResponse {
  slug: string;
  title: string;
  content: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UserResponse {
  id: number;
  email: string;
  is_active: boolean;
}

export interface ValidationErrorItem {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiErrorBody {
  detail: string | ValidationErrorItem[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | null;

  constructor(message: string, status: number, body: ApiErrorBody | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export interface RequestOptions {
  credentials?: RequestCredentials;
}

export interface PollChatJobOptions {
  intervalMs?: number;
  maxAttempts?: number;
  signal?: AbortSignal;
}
