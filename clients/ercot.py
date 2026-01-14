import datetime
import requests
from typing import Dict, List, Tuple
from matplotlib import pyplot as plt
from logger import get_logger

logger = get_logger(__name__)

class Ercot:
    FIGURE_SIZE = (8, 6)
    CHART_START_ANGLE = 140
    RENEWABLE_SOURCES = {'Hydro', 'Nuclear', 'Other', 'Power Storage', 'Solar', 'Wind'}
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S-%f'
    DISPLAY_DATE_FORMAT = '%b %d, %Y %I:%M %p'
    ERCOT_API_URL = 'https://www.ercot.com/api/1/services/read/dashboards/fuel-mix.json'

    def __init__(self, image_file: str = None) -> None:
        """
        Initialize the FuelMix class.

        :param image_file: Path to the image file where the fuel mix chart will be saved.
        """
        self.image_file = image_file or 'ercot_mix.png'
        self.timestamp: str = ""
        self.mix: Dict = {}
        self.pct_renewable: float = 0.0
        self.title: str = ""
        self.message: str = ""

    def __enter__(self) -> 'Ercot':
        logger.debug('Enter Ercot')
        self._process_gen_data()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        logger.debug('Exit Ercot')
        pass

    def _process_gen_data(self) -> None:
        """Process fuel mix data and generate visualization."""
        self._fetch_fuel_mix()
        self._calculate_renewables()
        self._generate_text()

    def _fetch_fuel_mix(self) -> None:
        """Fetch and extract the current generation mix from ERCOT API."""
        logger.debug('_fetch_fuel_mix')
        response = requests.get(self.ERCOT_API_URL)
        data = response.json()['data']

        # Get the current day's fuel mix
        current_day_key = list(data.keys())[-1]
        current_day_mix = data[current_day_key]
        current_mix_key = list(current_day_mix.keys())[-1]

        # Get the current time mix
        self.mix =  current_day_mix[current_mix_key]
        self.timestamp = current_mix_key
        logger.info(f'_fetch_fuel_mix {self.timestamp}')

    def _calculate_renewables(self) -> None:
        """Calculate the percentage of renewable energy in the mix."""
        total_mw = sum(entry['gen'] for entry in self.mix.values())
        renewable_mw = sum(
            entry['gen'] for key, entry in self.mix.items()
            if key in self.RENEWABLE_SOURCES)

        self.pct_renewable = (renewable_mw / total_mw * 100) if total_mw else 0
        logger.info(f"{renewable_mw:.0f}/{total_mw:.0f} {self.pct_renewable:.0f}% renewable")

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

    def _generate_text(self) -> str:
        """Generate formatted chart title with timestamp."""
        dt = datetime.datetime.strptime(self.timestamp, self.DATE_FORMAT)
        formatted_date = dt.strftime(self.DISPLAY_DATE_FORMAT)
        self.title = f"ERCOT Energy Mix as of {formatted_date} ({self.pct_renewable:.1f}% Renewable)"
        self.message = f"Currently ERCOT is running on {self.pct_renewable:.2f}% renewable energy. #Texas #ERCOT #Renewables"

    def _get_png_file_name(self) -> str:
        return f'{self.timestamp}.png'

    def create_visualization(self) -> None:
        """Generate and save the pie chart visualization."""
        _, values, legend_labels, explodes = self._prepare_chart_data()

        # remove negative values
        values = [max(value, 0) for value in values]

        plt.figure(figsize=self.FIGURE_SIZE)
        colors = plt.get_cmap('tab20').colors
        wedges, _ = plt.pie(values, explode=explodes ,colors=colors, startangle=self.CHART_START_ANGLE)

        img_file = f'{self.timestamp}.png' if self.timestamp else self.image_file
        img_file = f'out/{img_file}'

        plt.title(self.title)
        plt.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5))
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(img_file, bbox_inches='tight')
        plt.close()
        logger.info(f"Created visualization: {img_file}")
