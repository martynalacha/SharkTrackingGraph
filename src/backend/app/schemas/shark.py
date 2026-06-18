from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SharkBase(BaseModel):
    name: str = Field(..., examples=["Deep Blue"])
    species: str = Field(..., examples=["White Shark (Carcharodon carcharias)"])
    gender: str = Field(..., examples=["Female"])
    length: float = Field(..., gt=0, examples=[6.1])
    weight: float = Field(..., gt=0, examples=[2200.0])
    speciesImage: str = Field("", examples=["https://upload.wikimedia.org/wikipedia/commons/..."])


class SharkCreate(SharkBase):
    sharkId: str = Field(..., examples=["99999"])


class SharkUpdate(SharkBase):
    name: Optional[str] = None
    species: Optional[str] = None
    gender: Optional[str] = None
    length: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    speciesImage: Optional[str] = None

    # model_config = ConfigDict(from_attributes=True)


class SharkResponse(SharkCreate):
    weight: Optional[float] = None
    length: Optional[float] = None
    speciesImage: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
