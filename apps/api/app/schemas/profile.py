from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ProfileItemType, Visibility


class ProfileItemCreateRequest(BaseModel):
    key: str = Field(min_length=1, max_length=255)
    type: ProfileItemType
    label: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1)
    visibility: Visibility = Visibility.PRIVATE
    source: str | None = Field(default=None, max_length=255)
    sort_order: int = 0


class ProfileItemUpdateRequest(BaseModel):
    key: str = Field(min_length=1, max_length=255)
    type: ProfileItemType
    label: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1)
    visibility: Visibility
    source: str | None = Field(default=None, max_length=255)
    sort_order: int = 0


class ProfileItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    type: ProfileItemType
    label: str
    value: str
    visibility: Visibility
    source: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
