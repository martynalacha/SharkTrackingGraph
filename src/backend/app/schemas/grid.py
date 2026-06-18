from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OceanGridBase(BaseModel):
    centerLat: float = Field(..., ge=-90, le=90, examples=[34.5])
    centerLon: float = Field(..., ge=-180, le=180, examples=[-75.2])


class OceanGridCreate(OceanGridBase):
    gridId: str = Field(..., examples=["ZONE_999"])


class OceanGridUpdate(BaseModel):
    centerLat: Optional[float] = Field(None, ge=-90, le=90, examples=[34.5])
    centerLon: Optional[float] = Field(None, ge=-180, le=180, examples=[-75.2])

    model_config = ConfigDict(from_attributes=True)


class OceanGridResponse(OceanGridCreate):
    model_config = ConfigDict(from_attributes=True)
