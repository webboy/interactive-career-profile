from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LegalPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    content: str
    updated_at: datetime


class LegalPageUpdateRequest(BaseModel):
    title: str
    content: str
