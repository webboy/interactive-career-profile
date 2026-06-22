const SESSION_ID_KEY = "icp_public_session_id";
const CONVERSATION_ID_KEY = "icp_public_conversation_id";
const LANGUAGE_KEY = "icp_public_language";

export function getOrCreateSessionId(): string {
  const existing = localStorage.getItem(SESSION_ID_KEY);
  if (existing) {
    return existing;
  }
  const sessionId = crypto.randomUUID();
  localStorage.setItem(SESSION_ID_KEY, sessionId);
  return sessionId;
}

export function getStoredConversationId(): number | null {
  const raw = localStorage.getItem(CONVERSATION_ID_KEY);
  if (!raw) {
    return null;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

export function setStoredConversationId(conversationId: number | null): void {
  if (conversationId === null) {
    localStorage.removeItem(CONVERSATION_ID_KEY);
    return;
  }
  localStorage.setItem(CONVERSATION_ID_KEY, String(conversationId));
}

export function getStoredLanguage(): string | null {
  return localStorage.getItem(LANGUAGE_KEY);
}

export function setStoredLanguage(language: string): void {
  localStorage.setItem(LANGUAGE_KEY, language);
}

export function clearStoredConversationId(): void {
  localStorage.removeItem(CONVERSATION_ID_KEY);
}
