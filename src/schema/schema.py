from pydantic import BaseModel, ConfigDict


class SourceBase(BaseModel):
    name: str


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    id: int
    renewable: bool

    model_config = ConfigDict(from_attributes=True)


class GenSourceBase(BaseModel):
    gen: float


class GenSourceCreate(GenSourceBase):
    source_name: str


class GenSource(GenSourceBase):
    id: int
    gen_instant_id: int
    source_id: int

    model_config = ConfigDict(from_attributes=True)


class GenInstantBase(BaseModel):
    timestamp: str


class GenInstantCreate(GenInstantBase):
    sources: dict[str, float]


class GenInstant(GenInstantBase):
    id: int
    gen_sources: list[GenSource] = []

    model_config = ConfigDict(from_attributes=True)
