from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import EmailDeliveryStatus, LeadStatus, SourceCategory
from app.db.models.lead import FollowUpRequest, JobSubmission, MeetingRequest
from app.services.agent.context import build_context_text, summarize_used_sources
from app.services.email import EmailSender, EmailSendResult, get_email_sender
from app.services.retrieval.hybrid import HybridRetrievalResult, run_hybrid_retrieval


@dataclass(frozen=True)
class LeadEmailStatuses:
    admin_email_status: EmailDeliveryStatus
    requester_email_status: EmailDeliveryStatus
    admin_email_error: str | None = None
    requester_email_error: str | None = None


async def _send_lead_emails(
    *,
    settings: Settings,
    email_sender: EmailSender,
    admin_subject: str,
    admin_body: str,
    requester_email: str,
    requester_subject: str,
    requester_body: str,
) -> tuple[LeadEmailStatuses, LeadStatus]:
    admin_result = await email_sender.send_email(
        to_email=settings.admin_notification_email,
        subject=admin_subject,
        body=admin_body,
    )
    requester_result = await email_sender.send_email(
        to_email=requester_email,
        subject=requester_subject,
        body=requester_body,
    )

    lead_status = LeadStatus.SENT
    if (
        admin_result.status == EmailDeliveryStatus.FAILED
        or requester_result.status == EmailDeliveryStatus.FAILED
    ):
        lead_status = LeadStatus.FAILED

    return LeadEmailStatuses(
        admin_email_status=admin_result.status,
        requester_email_status=requester_result.status,
        admin_email_error=admin_result.error,
        requester_email_error=requester_result.error,
    ), lead_status


async def create_meeting_request(
    session: AsyncSession,
    *,
    requester_name: str,
    requester_email: str,
    organization: str | None = None,
    message: str | None = None,
    preferred_times: str | None = None,
    settings: Settings | None = None,
    email_sender: EmailSender | None = None,
) -> MeetingRequest:
    config = settings or get_settings()
    sender = email_sender or get_email_sender(config)

    meeting = MeetingRequest(
        requester_name=requester_name,
        requester_email=requester_email,
        organization=organization,
        message=message,
        preferred_times=preferred_times,
    )
    session.add(meeting)
    await session.flush()

    admin_body = (
        f"New meeting request #{meeting.id}\n\n"
        f"Name: {requester_name}\n"
        f"Email: {requester_email}\n"
        f"Organization: {organization or 'N/A'}\n"
        f"Preferred times: {preferred_times or 'N/A'}\n\n"
        f"Message:\n{message or 'N/A'}"
    )
    requester_body = (
        "Thank you for your meeting request. "
        "The profile owner has been notified and will follow up soon."
    )

    email_statuses, lead_status = await _send_lead_emails(
        settings=config,
        email_sender=sender,
        admin_subject=f"Meeting request from {requester_name}",
        admin_body=admin_body,
        requester_email=requester_email,
        requester_subject="Meeting request received",
        requester_body=requester_body,
    )

    meeting.status = lead_status
    meeting.admin_email_status = email_statuses.admin_email_status
    meeting.requester_email_status = email_statuses.requester_email_status
    meeting.admin_email_error = email_statuses.admin_email_error
    meeting.requester_email_error = email_statuses.requester_email_error

    await session.commit()
    await session.refresh(meeting)
    return meeting


async def create_follow_up_request(
    session: AsyncSession,
    *,
    requester_email: str,
    question: str,
    settings: Settings | None = None,
    email_sender: EmailSender | None = None,
) -> FollowUpRequest:
    config = settings or get_settings()
    sender = email_sender or get_email_sender(config)

    follow_up = FollowUpRequest(requester_email=requester_email, question=question)
    session.add(follow_up)
    await session.flush()

    admin_body = (
        f"New follow-up question #{follow_up.id}\n\n"
        f"Email: {requester_email}\n\n"
        f"Question:\n{question}"
    )
    requester_body = (
        "Thank you for your follow-up question. "
        "The profile owner has been notified."
    )

    email_statuses, lead_status = await _send_lead_emails(
        settings=config,
        email_sender=sender,
        admin_subject="Follow-up question received",
        admin_body=admin_body,
        requester_email=requester_email,
        requester_subject="Follow-up question received",
        requester_body=requester_body,
    )

    follow_up.status = lead_status
    follow_up.admin_email_status = email_statuses.admin_email_status
    follow_up.requester_email_status = email_statuses.requester_email_status
    follow_up.admin_email_error = email_statuses.admin_email_error
    follow_up.requester_email_error = email_statuses.requester_email_error

    await session.commit()
    await session.refresh(follow_up)
    return follow_up


def _build_role_fit_summary(retrieval_result: HybridRetrievalResult) -> str:
    used_sources = [source for source in retrieval_result.sources if source.was_used]
    if not used_sources:
        return (
            "Insufficient public profile evidence to provide a detailed role-fit analysis. "
            "No pay assessment is included."
        )

    structured = [
        source for source in used_sources if source.source_type != SourceCategory.DOCUMENT_CHUNK
    ]
    documents = [
        source for source in used_sources if source.source_type == SourceCategory.DOCUMENT_CHUNK
    ]

    lines = [
        "Role-fit analysis based on public profile evidence (no pay assessment):",
    ]
    if structured:
        lines.append("Canonical structured matches:")
        for source in structured[:5]:
            lines.append(f"- {source.title}: {source.snippet}")
    if documents:
        lines.append("Supporting document evidence:")
        for source in documents[:3]:
            lines.append(f"- {source.title}: {source.snippet}")

    return "\n".join(lines)


async def create_job_submission(
    session: AsyncSession,
    *,
    requester_email: str,
    job_description: str,
    company: str | None = None,
    role_title: str | None = None,
    settings: Settings | None = None,
    email_sender: EmailSender | None = None,
    document_search_override=None,
) -> JobSubmission:
    config = settings or get_settings()
    sender = email_sender or get_email_sender(config)

    retrieval_query = role_title or job_description[:500]
    retrieval_result = await run_hybrid_retrieval(
        session,
        retrieval_query,
        settings=config,
        document_search_override=document_search_override,
    )
    role_fit_summary = _build_role_fit_summary(retrieval_result)

    submission = JobSubmission(
        requester_email=requester_email,
        company=company,
        role_title=role_title,
        job_description=job_description,
        role_fit_summary=role_fit_summary,
        retrieval_log_id=retrieval_result.retrieval_log_id,
    )
    session.add(submission)
    await session.flush()

    admin_body = (
        f"New job submission #{submission.id}\n\n"
        f"Email: {requester_email}\n"
        f"Company: {company or 'N/A'}\n"
        f"Role: {role_title or 'N/A'}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Role-fit summary:\n{role_fit_summary}"
    )
    requester_body = (
        "Thank you for submitting the job description.\n\n"
        f"{role_fit_summary}"
    )

    email_statuses, lead_status = await _send_lead_emails(
        settings=config,
        email_sender=sender,
        admin_subject="Job description submission received",
        admin_body=admin_body,
        requester_email=requester_email,
        requester_subject="Job submission received",
        requester_body=requester_body,
    )

    submission.status = lead_status
    submission.admin_email_status = email_statuses.admin_email_status
    submission.requester_email_status = email_statuses.requester_email_status
    submission.admin_email_error = email_statuses.admin_email_error
    submission.requester_email_error = email_statuses.requester_email_error

    await session.commit()
    await session.refresh(submission)
    return submission


async def list_meeting_requests(session: AsyncSession) -> list[MeetingRequest]:
    result = await session.execute(select(MeetingRequest).order_by(MeetingRequest.id.desc()))
    return list(result.scalars().all())


async def list_follow_up_requests(session: AsyncSession) -> list[FollowUpRequest]:
    result = await session.execute(select(FollowUpRequest).order_by(FollowUpRequest.id.desc()))
    return list(result.scalars().all())


async def list_job_submissions(session: AsyncSession) -> list[JobSubmission]:
    result = await session.execute(select(JobSubmission).order_by(JobSubmission.id.desc()))
    return list(result.scalars().all())
