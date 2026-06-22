from enum import StrEnum


class Visibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ProfileItemType(StrEnum):
    TEXT = "text"
    LINK = "link"
    EMAIL = "email"
    LOCATION = "location"
    LANGUAGE = "language"
    AVAILABILITY = "availability"
    OTHER = "other"


class CareerRecordType(StrEnum):
    EXPERIENCE = "experience"
    PROJECT = "project"
    SKILL = "skill"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    LANGUAGE = "language"
    ACHIEVEMENT = "achievement"
    LEADERSHIP = "leadership"
    AVAILABILITY = "availability"
    OTHER = "other"


class EmbeddingStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    NOT_REQUIRED = "not_required"


class DocumentSourceType(StrEnum):
    UPLOAD = "upload"
    PASTED_TEXT = "pasted_text"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    CHUNKED = "chunked"
    FAILED = "failed"


class DocumentFileType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    TEXT = "text"


class SourceCategory(StrEnum):
    PROFILE_ITEM = "profile_item"
    CAREER_RECORD = "career_record"
    DOCUMENT_CHUNK = "document_chunk"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCallStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class UnansweredPromptReason(StrEnum):
    NO_CONTEXT = "no_context"
    BELOW_THRESHOLD = "below_threshold"
    POLICY = "policy"
    OTHER = "other"


class AgentIntent(StrEnum):
    CAREER = "career"
    SKILLS = "skills"
    AVAILABILITY = "availability"
    CONTACT = "contact"
    SALARY = "salary"
    GENERAL = "general"
    UNSUPPORTED = "unsupported"
    MEETING_REQUEST = "meeting_request"
    FOLLOW_UP = "follow_up"
    JOB_SUBMISSION = "job_submission"
    SKILL_EVIDENCE = "skill_evidence"
    PROJECT_CASE_STUDY = "project_case_study"
    CV_RECOMMENDATION = "cv_recommendation"


class LeadStatus(StrEnum):
    NEW = "new"
    SENT = "sent"
    FAILED = "failed"
    REVIEWED = "reviewed"


class EmailDeliveryStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    REFUSE_SALARY = "refuse_salary"
    REFUSE_CONTACT = "refuse_contact"
    REFUSE_UNSUPPORTED = "refuse_unsupported"
    REFUSE_GROUNDING = "refuse_grounding"
