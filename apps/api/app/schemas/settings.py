from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
    is_secret: bool


class SettingUpdateRequest(BaseModel):
    value: str
    is_secret: bool = False
