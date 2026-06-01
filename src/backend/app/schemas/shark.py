from pydantic import BaseModel, Field


class SharkBase(BaseModel):
    name: str = Field(..., example="Deep Blue")
    species: str = Field(..., example="White Shark (Carcharodon carcharias)")
    gender: str = Field(..., example="Female")
    length: float = Field(..., example=6.1)
    weight: float = Field(..., example=2200.0)
    speciesImage: str = Field("", example="https://upload.wikimedia.org/wikipedia/commons/...")


class SharkCreate(SharkBase):
    sharkId: str = Field(..., example="99999")


class SharkUpdate(SharkBase):
    pass


class SharkResponse(SharkCreate):
    class Config:
        from_attributes = True
