from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin_user
from app.core.enums import DocumentStatus, Visibility
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.documents import (
    DocumentChunkResponse,
    DocumentChunkUpdateRequest,
    DocumentIngestionActionResponse,
    DocumentResponse,
    DocumentTextCreateRequest,
    DocumentUpdateRequest,
)
from app.services.documents import (
    DocumentUploadTooLargeError,
    chunk_document,
    create_text_document,
    create_uploaded_document,
    delete_document,
    extract_document_text,
    get_document,
    get_document_chunk,
    list_document_chunks,
    list_documents,
    request_document_embedding,
    retry_document_ingestion,
    update_document,
    update_document_chunk_visibility,
)

router = APIRouter(prefix="/api/admin/documents", tags=["admin-documents"])


async def _get_document_or_404(session: AsyncSession, document_id: int):
    document = await get_document(session, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("", response_model=list[DocumentResponse])
async def admin_list_documents(
    visibility: Visibility | None = Query(default=None),
    status: DocumentStatus | None = Query(default=None),
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentResponse]:
    documents = await list_documents(session, visibility=visibility, status=status)
    return [DocumentResponse.model_validate(document) for document in documents]


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def admin_upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    visibility: Visibility = Form(default=Visibility.DRAFT),
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    content = await file.read()
    document_title = title or file.filename

    try:
        document = await create_uploaded_document(
            session,
            title=document_title,
            filename=file.filename,
            content=content,
            mime_type=file.content_type,
            visibility=visibility,
        )
    except DocumentUploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return DocumentResponse.model_validate(document)


@router.post("/text", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_text_document(
    payload: DocumentTextCreateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    document = await create_text_document(session, payload)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def admin_get_document(
    document_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    document = await _get_document_or_404(session, document_id)
    return DocumentResponse.model_validate(document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def admin_update_document(
    document_id: int,
    payload: DocumentUpdateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    document = await _get_document_or_404(session, document_id)
    updated = await update_document(session, document, payload)
    return DocumentResponse.model_validate(updated)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_document(
    document_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    document = await _get_document_or_404(session, document_id)
    await delete_document(session, document)


@router.post("/{document_id}/extract", response_model=DocumentIngestionActionResponse)
async def admin_extract_document(
    document_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentIngestionActionResponse:
    document = await _get_document_or_404(session, document_id)
    extracted = await extract_document_text(session, document)
    return DocumentIngestionActionResponse(document=DocumentResponse.model_validate(extracted))


@router.post("/{document_id}/chunk", response_model=DocumentIngestionActionResponse)
async def admin_chunk_document(
    document_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentIngestionActionResponse:
    document = await _get_document_or_404(session, document_id)
    chunked, chunks_created = await chunk_document(session, document)
    return DocumentIngestionActionResponse(
        document=DocumentResponse.model_validate(chunked),
        chunks_created=chunks_created,
    )


@router.post("/{document_id}/retry-ingestion", response_model=DocumentIngestionActionResponse)
async def admin_retry_document_ingestion(
    document_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentIngestionActionResponse:
    document = await _get_document_or_404(session, document_id)
    retried, chunks_created = await retry_document_ingestion(session, document)
    return DocumentIngestionActionResponse(
        document=DocumentResponse.model_validate(retried),
        chunks_created=chunks_created,
    )


@router.post("/{document_id}/request-embedding", response_model=DocumentResponse)
async def admin_request_document_embedding(
    document_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    document = await _get_document_or_404(session, document_id)
    updated = await request_document_embedding(session, document)
    return DocumentResponse.model_validate(updated)


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def admin_list_document_chunks(
    document_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentChunkResponse]:
    await _get_document_or_404(session, document_id)
    chunks = await list_document_chunks(session, document_id)
    return [DocumentChunkResponse.model_validate(chunk) for chunk in chunks]


chunk_router = APIRouter(prefix="/api/admin/document-chunks", tags=["admin-document-chunks"])


@chunk_router.put("/{chunk_id}", response_model=DocumentChunkResponse)
async def admin_update_document_chunk(
    chunk_id: int,
    payload: DocumentChunkUpdateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentChunkResponse:
    chunk = await get_document_chunk(session, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")

    updated = await update_document_chunk_visibility(session, chunk, payload.visibility)
    return DocumentChunkResponse.model_validate(updated)
