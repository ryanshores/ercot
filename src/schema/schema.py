from pydantic import BaseModel


class SourceBase(BaseModel):
    name: str


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    id: int
    renewable: bool

    class Config:
        orm_mode = True


class GenSourceBase(SourceBase):
    gen: float


class GenSourceCreate(GenSourceBase):
    source_name: str


class GenSource(GenSourceBase):
    id: int
    gen_instant_id: int
    source_id: int

    class Config:
        orm_mode = True


class GenInstantBase(BaseModel):
    timestamp: str


class GenInstantCreate(GenInstantBase):
    sources: dict[str, float]


class GenInstant(GenInstantBase):
    id: int
    gen_sources: list[GenSource] = []

    class Config:
        orm_mode = True
