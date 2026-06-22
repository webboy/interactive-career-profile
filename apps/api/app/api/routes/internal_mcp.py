from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.internal_mcp import require_mcp_internal_token
from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.mcp_internal import (
    EvidenceQueryRequest,
    EvidenceToolResponse,
    FollowUpRequestCreate,
    FollowUpRequestResponse,
    JobSubmissionCreate,
    JobSubmissionResponse,
    MeetingRequestCreate,
    MeetingRequestResponse,
)
from app.services.leads import create_follow_up_request, create_job_submission, create_meeting_request
from app.services.mcp.evidence import run_evidence_tool

router = APIRouter(prefix="/api/internal/mcp", tags=["internal-mcp"])


@router.post("/meeting-requests", response_model=MeetingRequestResponse)
async def internal_create_meeting_request(
    payload: MeetingRequestCreate,
    _: None = Depends(require_mcp_internal_token),
    session: AsyncSession = Depends(get_db_session),
) -> MeetingRequestResponse:
    settings = get_settings()
    meeting = await create_meeting_request(
        session,
        requester_name=payload.requester_name,
        requester_email=str(payload.requester_email),
        organization=payload.organization,
        message=payload.message,
        preferred_times=payload.preferred_times,
        settings=settings,
    )
    return MeetingRequestResponse(
        id=meeting.id,
        status=meeting.status.value,
        admin_email_status=meeting.admin_email_status.value,
        requester_email_status=meeting.requester_email_status.value,
        requester_name=meeting.requester_name,
        requester_email=meeting.requester_email,
        organization=meeting.organization,
        message=meeting.message,
        preferred_times=meeting.preferred_times,
    )


@router.post("/follow-up-requests", response_model=FollowUpRequestResponse)
async def internal_create_follow_up_request(
    payload: FollowUpRequestCreate,
    _: None = Depends(require_mcp_internal_token),
    session: AsyncSession = Depends(get_db_session),
) -> FollowUpRequestResponse:
    settings = get_settings()
    follow_up = await create_follow_up_request(
        session,
        requester_email=str(payload.requester_email),
        question=payload.question,
        settings=settings,
    )
    return FollowUpRequestResponse(
        id=follow_up.id,
        status=follow_up.status.value,
        admin_email_status=follow_up.admin_email_status.value,
        requester_email_status=follow_up.requester_email_status.value,
        requester_email=follow_up.requester_email,
        question=follow_up.question,
    )


@router.post("/job-submissions", response_model=JobSubmissionResponse)
async def internal_create_job_submission(
    payload: JobSubmissionCreate,
    _: None = Depends(require_mcp_internal_token),
    session: AsyncSession = Depends(get_db_session),
) -> JobSubmissionResponse:
    settings = get_settings()
    submission = await create_job_submission(
        session,
        requester_email=str(payload.requester_email),
        job_description=payload.job_description,
        company=payload.company,
        role_title=payload.role_title,
        settings=settings,
    )
    return JobSubmissionResponse(
        id=submission.id,
        status=submission.status.value,
        admin_email_status=submission.admin_email_status.value,
        requester_email_status=submission.requester_email_status.value,
        requester_email=submission.requester_email,
        company=submission.company,
        role_title=submission.role_title,
        job_description=submission.job_description,
        role_fit_summary=submission.role_fit_summary,
        retrieval_log_id=submission.retrieval_log_id,
    )


@router.post("/recommend-profile", response_model=EvidenceToolResponse)
async def internal_recommend_profile(
    payload: EvidenceQueryRequest,
    _: None = Depends(require_mcp_internal_token),
    session: AsyncSession = Depends(get_db_session),
) -> EvidenceToolResponse:
    settings = get_settings()
    result = await run_evidence_tool(
        session,
        payload.query,
        settings=settings,
        intent_hints=["skills", "experience", *payload.intent_hints],
    )
    return EvidenceToolResponse(
        query=result.query,
        summary=result.summary,
        retrieval_log_id=result.retrieval_log_id,
        sources=result.sources,
        had_usable_context=result.had_usable_context,
    )


@router.post("/skill-evidence", response_model=EvidenceToolResponse)
async def internal_skill_evidence(
    payload: EvidenceQueryRequest,
    _: None = Depends(require_mcp_internal_token),
    session: AsyncSession = Depends(get_db_session),
) -> EvidenceToolResponse:
    settings = get_settings()
    result = await run_evidence_tool(
        session,
        payload.query,
        settings=settings,
        intent_hints=payload.intent_hints,
    )
    return EvidenceToolResponse(
        query=result.query,
        summary=result.summary,
        retrieval_log_id=result.retrieval_log_id,
        sources=result.sources,
        had_usable_context=result.had_usable_context,
    )


@router.post("/project-case-study", response_model=EvidenceToolResponse)
async def internal_project_case_study(
    payload: EvidenceQueryRequest,
    _: None = Depends(require_mcp_internal_token),
    session: AsyncSession = Depends(get_db_session),
) -> EvidenceToolResponse:
    settings = get_settings()
    result = await run_evidence_tool(
        session,
        payload.query,
        settings=settings,
        intent_hints=["experience", "project", *payload.intent_hints],
    )
    return EvidenceToolResponse(
        query=result.query,
        summary=result.summary,
        retrieval_log_id=result.retrieval_log_id,
        sources=result.sources,
        had_usable_context=result.had_usable_context,
    )
