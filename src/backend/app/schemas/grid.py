from pydantic import BaseModel, Field


class OceanGridBase(BaseModel):
    centerLat: float = Field(..., example=34.5)
    centerLon: float = Field(..., example=-75.2)


class OceanGridCreate(OceanGridBase):
    gridId: str = Field(..., example="ZONE_999")


class OceanGridResponse(OceanGridCreate):
    class Config:
        from_attributes = True
