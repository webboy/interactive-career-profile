from pydantic import BaseModel, EmailStr, Field


class MeetingRequestCreate(BaseModel):
    requester_name: str = Field(min_length=1, max_length=255)
    requester_email: EmailStr
    organization: str | None = Field(default=None, max_length=255)
    message: str | None = None
    preferred_times: str | None = None


class FollowUpRequestCreate(BaseModel):
    requester_email: EmailStr
    question: str = Field(min_length=1)


class JobSubmissionCreate(BaseModel):
    requester_email: EmailStr
    job_description: str = Field(min_length=1)
    company: str | None = Field(default=None, max_length=255)
    role_title: str | None = Field(default=None, max_length=255)


class EvidenceQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    intent_hints: list[str] = Field(default_factory=list)


class LeadResponse(BaseModel):
    id: int
    status: str
    admin_email_status: str
    requester_email_status: str


class MeetingRequestResponse(LeadResponse):
    requester_name: str
    requester_email: str
    organization: str | None = None
    message: str | None = None
    preferred_times: str | None = None


class FollowUpRequestResponse(LeadResponse):
    requester_email: str
    question: str


class JobSubmissionResponse(LeadResponse):
    requester_email: str
    company: str | None = None
    role_title: str | None = None
    job_description: str
    role_fit_summary: str | None = None
    retrieval_log_id: int | None = None


class EvidenceToolResponse(BaseModel):
    query: str
    summary: str
    retrieval_log_id: int | None = None
    sources: list[dict[str, str | bool]] = Field(default_factory=list)
    had_usable_context: bool
