from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin_user
from app.db.models.conversation import ToolCall
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.leads import ToolCallResponse, ToolCallsListResponse
from app.schemas.mcp_internal import (
    FollowUpRequestResponse,
    JobSubmissionResponse,
    MeetingRequestResponse,
)
from app.services.leads import list_follow_up_requests, list_job_submissions, list_meeting_requests

router = APIRouter(prefix="/api/admin", tags=["admin-leads"])


@router.get("/leads/meeting-requests", response_model=list[MeetingRequestResponse])
async def admin_list_meeting_requests(
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[MeetingRequestResponse]:
    meetings = await list_meeting_requests(session)
    return [
        MeetingRequestResponse(
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
        for meeting in meetings
    ]


@router.get("/leads/follow-up-requests", response_model=list[FollowUpRequestResponse])
async def admin_list_follow_up_requests(
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[FollowUpRequestResponse]:
    follow_ups = await list_follow_up_requests(session)
    return [
        FollowUpRequestResponse(
            id=follow_up.id,
            status=follow_up.status.value,
            admin_email_status=follow_up.admin_email_status.value,
            requester_email_status=follow_up.requester_email_status.value,
            requester_email=follow_up.requester_email,
            question=follow_up.question,
        )
        for follow_up in follow_ups
    ]


@router.get("/leads/job-submissions", response_model=list[JobSubmissionResponse])
async def admin_list_job_submissions(
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[JobSubmissionResponse]:
    submissions = await list_job_submissions(session)
    return [
        JobSubmissionResponse(
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
        for submission in submissions
    ]


@router.get("/tool-calls", response_model=ToolCallsListResponse)
async def admin_list_tool_calls(
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> ToolCallsListResponse:
    result = await session.execute(select(ToolCall).order_by(ToolCall.id.desc()))
    tool_calls = list(result.scalars().all())
    return ToolCallsListResponse(
        tool_calls=[
            ToolCallResponse(
                id=tool_call.id,
                conversation_id=tool_call.conversation_id,
                tool_name=tool_call.tool_name,
                status=tool_call.status.value,
                request_payload=tool_call.request_payload,
                response_payload=tool_call.response_payload,
                error_message=tool_call.error_message,
            )
            for tool_call in tool_calls
        ]
    )
