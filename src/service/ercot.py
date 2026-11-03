from datetime import datetime
from typing import Dict, Any

import requests

from src.db.database import SessionLocal
from src.logger.logger import get_logger
from src.schema import schema
from src.service.db.gen_instant import create_gen_instances

logger = get_logger(__name__)


def _latest_key(mapping: Dict[str, Any]) -> str:
    if not mapping:
        raise ValueError("ERCOT API returned an empty data structure.")
    return max(mapping.keys())


class Ercot:
    RENEWABLE_SOURCES = {'Hydro', 'Nuclear', 'Other', 'Power Storage', 'Solar', 'Wind'}
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S-%f'
    DISPLAY_DATE_FORMAT = '%b %d, %Y %I:%M %p'
    ERCOT_API_URL = 'https://www.ercot.com/api/1/services/read/dashboards/fuel-mix.json'
    REQUEST_TIMEOUT_SECONDS = 15

    FUEL_KEYS = {
        "coal": "Coal and Lignite",
        "hydro": "Hydro",
        "natural_gas": "Natural Gas",
        "nuclear": "Nuclear",
        "other": "Other",
        "power_storage": "Power Storage",
        "solar": "Solar",
        "wind": "Wind",
    }

    def __init__(self) -> None:
        self.timestamp: str = ""
        self.mix: Dict[str, Dict[str, Any]] = {}
        self.title: str = ""
        self.message: str = ""

        self.coal: float = 0.0
        self.hydro: float = 0.0
        self.natural_gas: float = 0.0
        self.nuclear: float = 0.0
        self.other: float = 0.0
        self.power_storage: float = 0.0
        self.solar: float = 0.0
        self.wind: float = 0.0

    def __enter__(self) -> 'Ercot':
        logger.debug('')
        self._process_gen_data()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        logger.debug('')

    @property
    def renewable_gen(self) -> float:
        return self.hydro + self.nuclear + self.power_storage + self.solar + self.wind

    @property
    def total_gen(self) -> float:
        return (
                self.coal
                + self.hydro
                + self.natural_gas
                + self.nuclear
                + self.other
                + self.power_storage
                + self.solar
                + self.wind
        )

    @property
    def renewable_pct(self) -> float:
        return self.renewable_gen / self.total_gen * 100 if self.total_gen else 0

    def _process_gen_data(self) -> None:
        """Fetch and persist fuel mix data."""
        self._fetch_fuel_mix()
        self._generate_text()

    def _fetch_fuel_mix(self) -> None:
        """Fetch and extract the current generation mix from ERCOT API."""
        logger.debug('')
        response = requests.get(self.ERCOT_API_URL, timeout=self.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()['data']

        self._process_gen_mixes(data)

        # Get the most recent day's fuel mix
        current_day_key = _latest_key(data)
        current_day_mix = data[current_day_key]

        # Get the most recent time mix
        current_mix_key = _latest_key(current_day_mix)
        self.mix = current_day_mix[current_mix_key]
        self.timestamp = current_mix_key

        # Populate fields from the response using a single source of truth for keys
        self.coal = float(self.mix[self.FUEL_KEYS["coal"]]['gen'])
        self.hydro = float(self.mix[self.FUEL_KEYS["hydro"]]['gen'])
        self.natural_gas = float(self.mix[self.FUEL_KEYS["natural_gas"]]['gen'])
        self.nuclear = float(self.mix[self.FUEL_KEYS["nuclear"]]['gen'])
        self.other = float(self.mix[self.FUEL_KEYS["other"]]['gen'])
        self.power_storage = float(self.mix[self.FUEL_KEYS["power_storage"]]['gen'])
        self.solar = float(self.mix[self.FUEL_KEYS["solar"]]['gen'])
        self.wind = float(self.mix[self.FUEL_KEYS["wind"]]['gen'])

        logger.info(
            f'{self.renewable_gen:.1f}/{self.total_gen:.1f}MW {self.renewable_pct:.1f}% Renewable ({self.timestamp})')

    def _process_gen_mixes(self, data: Dict[str, Any]):
        gen_instants = []
        for day in data.values():
            for timestamp, mix_data in day.items():
                # ERCOT also supplies a charging/discharging breakdown. The net
                # Power Storage field already includes it; do not count it twice.
                mix = {
                    key: value['gen'] for key, value in mix_data.items()
                    if key not in {'Power Storage Charging', 'Power Storage Discharging'}
                }
                gen_instants.append(schema.GenInstantCreate(
                    timestamp=timestamp,
                    sources=mix
                ))
        with SessionLocal() as db:
            created_instances = create_gen_instances(db, gen_instants)
            logger.info("Saved gen instances for %d timestamps", len(created_instances))

    def _generate_text(self) -> None:
        """Generate formatted chart title with timestamp."""
        dt = datetime.strptime(self.timestamp, self.DATE_FORMAT)
        formatted_date = dt.strftime(self.DISPLAY_DATE_FORMAT)
        self.title = (
            f"ERCOT Energy Mix | {formatted_date} using {self.total_gen:.1f} MW "
            f"({self.renewable_pct:.1f}% Renewable)"
        )
        self.message = (
            f"Currently ERCOT is running on {self.renewable_pct:.2f}% renewable energy. "
            f"#Texas #ERCOT #Renewables"
        )
