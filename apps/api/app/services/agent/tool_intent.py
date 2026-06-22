import re

from app.core.enums import AgentIntent

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
NAME_PATTERN = re.compile(r"(?:my name is|i am|i'm)\s+([A-Za-z][A-Za-z\s'.-]{1,60})", re.IGNORECASE)
ORGANIZATION_PATTERN = re.compile(
    r"(?:organization|company|from)\s*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
PREFERRED_TIMES_PATTERN = re.compile(
    r"(?:preferred times?|availability)\s*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
JOB_DESCRIPTION_PATTERN = re.compile(
    r"job description\s*:\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)
ROLE_TITLE_PATTERN = re.compile(r"(?:role|position|title)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
COMPANY_PATTERN = re.compile(r"company\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

MEETING_PATTERN = re.compile(
    r"\b(schedule|book|request)\s+(a\s+)?meeting\b|\bmeeting\s+request\b",
    re.IGNORECASE,
)
FOLLOW_UP_PATTERN = re.compile(
    r"\bfollow[\s-]?up\b|\bsend\s+(my\s+)?question\b|\bforward\s+(my\s+)?question\b",
    re.IGNORECASE,
)
JOB_SUBMISSION_PATTERN = re.compile(
    r"\bsubmit\s+(this\s+)?job\b|\brole[\s-]?fit\b|\bjob\s+submission\b",
    re.IGNORECASE,
)
SKILL_EVIDENCE_PATTERN = re.compile(
    r"\bskill evidence\b|\bevidence for\b.*\bskill\b|\bprove\b.*\bskill\b",
    re.IGNORECASE,
)
PROJECT_CASE_STUDY_PATTERN = re.compile(
    r"\bcase study\b|\bproject case study\b|\bproject evidence\b",
    re.IGNORECASE,
)
CV_RECOMMENDATION_PATTERN = re.compile(
    r"\brecommend\b.*\b(cv|profile|resume)\b|\b(cv|profile|resume)\b.*\brecommend",
    re.IGNORECASE,
)


def extract_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def extract_name(text: str, fallback: str = "Requester") -> str:
    match = NAME_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return fallback


def extract_block(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None


def classify_tool_intent(user_message: str) -> AgentIntent | None:
    if MEETING_PATTERN.search(user_message):
        return AgentIntent.MEETING_REQUEST
    if FOLLOW_UP_PATTERN.search(user_message):
        return AgentIntent.FOLLOW_UP
    if JOB_SUBMISSION_PATTERN.search(user_message):
        return AgentIntent.JOB_SUBMISSION
    if SKILL_EVIDENCE_PATTERN.search(user_message):
        return AgentIntent.SKILL_EVIDENCE
    if PROJECT_CASE_STUDY_PATTERN.search(user_message):
        return AgentIntent.PROJECT_CASE_STUDY
    if CV_RECOMMENDATION_PATTERN.search(user_message):
        return AgentIntent.CV_RECOMMENDATION
    return None


def build_tool_arguments(intent: AgentIntent, user_message: str) -> dict[str, str]:
    email = extract_email(user_message) or "requester@example.com"

    if intent == AgentIntent.MEETING_REQUEST:
        return {
            "requester_name": extract_name(user_message),
            "requester_email": email,
            "organization": extract_block(ORGANIZATION_PATTERN, user_message) or "",
            "message": user_message.strip(),
            "preferred_times": extract_block(PREFERRED_TIMES_PATTERN, user_message) or "",
        }

    if intent == AgentIntent.FOLLOW_UP:
        return {
            "requester_email": email,
            "question": user_message.strip(),
        }

    if intent == AgentIntent.JOB_SUBMISSION:
        job_description = extract_block(JOB_DESCRIPTION_PATTERN, user_message) or user_message.strip()
        return {
            "requester_email": email,
            "job_description": job_description,
            "company": extract_block(COMPANY_PATTERN, user_message) or "",
            "role_title": extract_block(ROLE_TITLE_PATTERN, user_message) or "",
        }

    query = user_message.strip()
    if intent == AgentIntent.SKILL_EVIDENCE:
        return {"query": query}
    if intent == AgentIntent.PROJECT_CASE_STUDY:
        return {"query": query, "intent_hints": ["project", "experience"]}
    if intent == AgentIntent.CV_RECOMMENDATION:
        return {"query": query, "intent_hints": ["skills", "experience"]}

    return {"query": query}


def tool_name_for_intent(intent: AgentIntent) -> str:
    mapping = {
        AgentIntent.MEETING_REQUEST: "request_meeting",
        AgentIntent.FOLLOW_UP: "send_follow_up_question",
        AgentIntent.JOB_SUBMISSION: "submit_job_description",
        AgentIntent.SKILL_EVIDENCE: "get_skill_evidence",
        AgentIntent.PROJECT_CASE_STUDY: "get_project_case_study",
        AgentIntent.CV_RECOMMENDATION: "recommend_cv_profile",
    }
    return mapping[intent]


def format_tool_response(intent: AgentIntent, payload: dict[str, object]) -> str:
    if intent == AgentIntent.MEETING_REQUEST:
        return (
            "Your meeting request has been recorded and notification emails were queued. "
            f"Reference ID: {payload.get('id')}."
        )
    if intent == AgentIntent.FOLLOW_UP:
        return (
            "Your follow-up question has been forwarded to the profile owner. "
            f"Reference ID: {payload.get('id')}."
        )
    if intent == AgentIntent.JOB_SUBMISSION:
        summary = payload.get("role_fit_summary") or "Role-fit analysis is being prepared."
        return f"Job submission received.\n\n{summary}"
    summary = payload.get("summary") or "No verified evidence was found."
    return str(summary)
