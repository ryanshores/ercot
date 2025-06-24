import datetime
import requests

from matplotlib import pyplot as plt
from ercot import ERCOT_API_URL, IMAGE_FILE

class FuelMix:
    def __init__(self, image_file=IMAGE_FILE):
        """
        Initialize the FuelMix class.

        :param image_file: Path to the image file where the fuel mix chart will be saved.
        """
        self.image_file = image_file
        self.image_label = None
        self.mix = None
        self.pct_renewable = None

        self.fetch_fuel_mix()

    def __enter__(self):
        self.fetch_fuel_mix()
        self.calculate_renewables()
        self.generate_pie_chart_legend()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def fetch_fuel_mix(self):
        """
        Fetch the current fuel mix from the ERCOT API.

        :return: Dictionary containing the current fuel mix.
        """
        response = requests.get(ERCOT_API_URL)
        data = response.json()['data']

        # Get the current day's fuel mix
        current_day_key = list(data.keys())[-1]
        current_day_mix = data[current_day_key]

        # Get the current time mix
        current_mix_key = list(current_day_mix.keys())[-1]
        self.mix =  current_day_mix[current_mix_key]
        self.image_label = current_mix_key

    def calculate_renewables(self):
        # Calculate the percentage of renewable energy in the mix
        total_mw = sum(entry['gen'] for entry in self.mix.values())

        renewable_types = ['Hydro', 'Nuclear', 'Other', 'Power Storage', 'Solar', 'Wind']
        renewable_mw = sum(entry['gen'] for key, entry in self.mix.items() if key in renewable_types)

        pct_renewable = renewable_mw / total_mw * 100 if total_mw else 0
        self.pct_renewable = pct_renewable

    def generate_pie_chart_legend(self):
        labels = [key for key, entry in self.mix.items()]
        values = [entry['gen'] for entry in self.mix.values()]
        total = sum(values)
        colors = plt.get_cmap('tab20').colors

        # Create human-readable labels for legend: "Fuel: XX.X%"
        legend_labels = [f"{label}: {value / total * 100:.1f}%" for label, value in zip(labels, values)]

        plt.figure(figsize=(8, 6))  # Wider layout for legend
        wedges, _ = plt.pie(values, colors=colors, startangle=140)

        dt = datetime.datetime.strptime(self.image_label, '%Y-%m-%d %H:%M:%S-%f')
        formatted_date = dt.strftime('%b %d, %Y %I:%M %p')

        title = f"ERCOT Energy Mix as of {formatted_date} ({self.pct_renewable:.1f}% Renewable)"

        plt.title(title)
        plt.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5))
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(IMAGE_FILE, bbox_inches='tight')
        plt.close()