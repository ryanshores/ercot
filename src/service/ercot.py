from datetime import datetime
from typing import Dict, List, Tuple, Any

import numpy as np
import requests
from matplotlib import pyplot as plt

from src.logger.logger import get_logger

logger = get_logger(__name__)


def _latest_key(mapping: Dict[str, Any]) -> str:
    if not mapping:
        raise ValueError("ERCOT API returned an empty data structure.")
    return max(mapping.keys())


class Ercot:
    FIGURE_SIZE = (8, 6)
    CHART_START_ANGLE = 140
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

    def __init__(self, image_file: str = None) -> None:
        """
        Initialize the FuelMix class.

        :param image_file: Path to the image file where the fuel mix chart will be saved.
        """
        self.image_file = image_file or 'ercot_mix.png'
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

    @property
    def png_file_name(self) -> str:
        return f'{self.timestamp}.png'

    def _output_path(self) -> str:
        file_name = self.png_file_name if self.timestamp else self.image_file
        return f'out/{file_name}'

    def _process_gen_data(self) -> None:
        """Process fuel mix data and generate visualization."""
        self._fetch_fuel_mix()
        self._generate_text()

    def _fetch_fuel_mix(self) -> None:
        """Fetch and extract the current generation mix from ERCOT API."""
        logger.debug('')
        response = requests.get(self.ERCOT_API_URL, timeout=self.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()['data']

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

    def _prepare_chart_data(self) -> Tuple[List[str], List[float], List[str], List[float]]:
        """Prepare data for chart visualization."""
        labels = list(self.mix.keys())
        values = [entry['gen'] for entry in self.mix.values()]
        total = sum(values)
        legend_labels = [
            f"{label}: {value / total * 100:.1f}%"
            for label, value in zip(labels, values)
        ]
        explodes = [0.1 if label not in self.RENEWABLE_SOURCES else 0 for label in labels]
        return labels, values, legend_labels, explodes

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

    def create_visualization(self) -> None:
        """Generate and save the pie chart visualization."""
        _, values, legend_labels, explodes = self._prepare_chart_data()

        # remove negative values
        values = [max(value, 0) for value in values]

        plt.figure(figsize=self.FIGURE_SIZE)
        cmap = plt.get_cmap("tab20")
        colors = cmap(np.linspace(0, 1, 20))  # (20, 4) RGBA array
        wedges, _ = plt.pie(values, explode=explodes, colors=colors, startangle=self.CHART_START_ANGLE)

        img_file = self._output_path()

        plt.title(self.title)
        plt.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5))
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(img_file, bbox_inches='tight')
        plt.close()
        logger.info(f"Created visualization: {img_file}")
