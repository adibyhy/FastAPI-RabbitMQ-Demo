from datetime import datetime
from typing import List

from pydantic import (
    BaseModel,
    validator,
)


class PredsModel(BaseModel):
    image_frame: str
    prob: float
    tags: List[str]

    def __getitem__(self, item):
        return getattr(self, item)


class DataModel(BaseModel):
    license_id: str
    preds: List[PredsModel]

    def __getitem__(self, item):
        return getattr(self, item)


class PayloadModel(BaseModel):
    device_id: str
    client_id: str
    created_at: str
    data: DataModel

    @validator("created_at")
    def timestamp_format(cls, v):
        """Make sure the timestamp format is correct"""
        try:
            timestamp = datetime.strptime(v, "%Y-%m-%d %H:%M:%S.%f")
        except:
            raise
        return v
