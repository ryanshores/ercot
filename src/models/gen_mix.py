from sqlalchemy import Column, String, Float

from src.models.shared import EntityBase


class GenMix(EntityBase):
    __tablename__ = "gen_mix"

    timestamp = Column(String, index=True, unique=True)
    coal = Column(Float)
    hydro = Column(Float)
    nuclear = Column(Float)
    natural_gas = Column(Float)
    other = Column(Float)
    power_storage = Column(Float)
    solar = Column(Float)
    wind = Column(Float)
    gen_total = Column(Float)
    gen_renewable = Column(Float)
    percentage_renewable = Column(Float)

    def __init__(self, timestamp: String, coal: float, hydro: float, nuclear: float, natural_gas: float, other: float,
                 power_storage: float, solar: float, wind: float) -> None:
        super().__init__()
        self.timestamp = timestamp
        self.coal = coal
        self.hydro = hydro
        self.nuclear = nuclear
        self.natural_gas = natural_gas
        self.other = other
        self.power_storage = power_storage
        self.solar = solar
        self.wind = wind
        self.gen_total = coal + hydro + nuclear + natural_gas + other + power_storage + solar + wind
        self.gen_renewable = hydro + nuclear + other + power_storage + solar + wind
        self.percentage_renewable = self.gen_renewable / self.gen_total * 100 if self.gen_total else 0

    def __repr__(self) -> str:
        return f"<GenMix {self.timestamp}> {self.gen_renewable}/{self.gen_total}MW {self.percentage_renewable:.1f}% Renewable"
