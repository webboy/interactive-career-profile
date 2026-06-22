from pydantic import BaseModel, Field


class DocumentChunkEmbeddingActionResponse(BaseModel):
    chunk_id: int
    embedding_status: str
    embedding_error: str | None = None


class RunPendingEmbeddingsResponse(BaseModel):
    processed: int
    failed: int
    requested: int
