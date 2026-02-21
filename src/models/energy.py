from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from src.models.shared import EntityBase

energy_sources = {
    "Coal and Lignite": {
        "name": "coal",
        "display": "Coal",
        "color": "#000000",
        "renewable": False,
    },
    "Hydro": {
        "name": "hydro",
        "display": "Hydro",
        "color": "#36A2EB",
        "renewable": True,
    },
    "Natural Gas": {
        "name": "natural_gas",
        "display": "Natural Gas",
        "color": "#9966FF",
        "renewable": False,
    },
    "Nuclear": {
        "name": "nuclear",
        "display": "Nuclear",
        "color": "#FFCD56",
        "renewable": True,
    },
    "Other": {
        "name": "other",
        "display": "Other",
        "color": "#C9CBCF",
        "renewable": True,
    },
    "Power Storage": {
        "name": "power_storage",
        "display": "Power Storage",
        "color": "#FF6384",
        "renewable": True,
    },
    "Solar": {
        "name": "solar",
        "display": "Solar",
        "color": "#FF9F40",
        "renewable": True,
    },
    "Wind": {"name": "wind", "display": "Wind", "color": "#4BC0C0", "renewable": True},
}


class Source(EntityBase):
    __tablename__ = "source"

    name = Column(String, unique=True, nullable=False)
    renewable = Column(Boolean, nullable=False, default=False)

    gen_sources = relationship("GenSource", back_populates="source")

    @staticmethod
    def metadata_for(name: str) -> dict:
        source_meta = energy_sources.get(name)
        if not source_meta:
            raise ValueError(f"Invalid energy source: {name}")
        return source_meta

    def __init__(self, name: str) -> None:
        super().__init__()
        source_meta = self.metadata_for(name)
        self.name = source_meta["name"]
        self.renewable = source_meta["renewable"]


class GenSource(EntityBase):
    __tablename__ = "gen_source"

    gen = Column(Float, nullable=False, default=0.0)

    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    gen_instant_id = Column(Integer, ForeignKey("gen_instant.id"), nullable=False)

    source = relationship("Source", back_populates="gen_sources")
    gen_instant = relationship("GenInstant", back_populates="gen_sources")

    def __init__(self, gen: float, source: Source) -> None:
        super().__init__()
        self.gen = gen
        self.source = source


class GenInstant(EntityBase):
    __tablename__ = "gen_instant"

    timestamp = Column(String, index=True, unique=True)

    gen_sources = relationship(
        "GenSource",
        back_populates="gen_instant",
        cascade="all, delete-orphan",
    )

    def __init__(self, timestamp: str, gen_sources: list[GenSource]) -> None:
        super().__init__()
        self.timestamp = timestamp
        self.gen_sources = gen_sources

        # Compute derived values
        self.gen_total = sum(gs.gen for gs in self.gen_sources)
        self.gen_renewables = sum(
            gs.gen for gs in self.gen_sources if gs.source.renewable
        )
        self.percentage_renewable = (
            self.gen_renewables / self.gen_total * 100 if self.gen_total else 0
        )
