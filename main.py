import matplotlib.pyplot as plt
import os
import requests
import schedule
import time
import traceback
import tweepy

from dotenv import load_dotenv

load_dotenv()

# ==== CONFIG ====
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET')

ERCOT_API_URL = 'https://www.ercot.com/api/1/services/read/dashboards/fuel-mix.json'
IMAGE_FILE = 'ercot_mix.png'

# ==== FUNCTIONS ====

def fetch_fuel_mix():
    response = requests.get(ERCOT_API_URL)
    data = response.json()['data']

    # get the current day's fuel mix
    current_day_key = list(data.keys())[-1]
    current_day_mix = data[current_day_key]

    # get the current time mix
    current_mix_key = list(current_day_mix.keys())[-1]
    return current_day_mix[current_mix_key]

def calculate_renewables(mix):
    # Calculate the percentage of renewable energy in the mix
    total_mw = sum(entry['gen'] for entry in mix.values())

    renewable_types = ['Hydro', 'Nuclear', 'Power Storage', 'Solar', 'Wind']
    renewable_mw = sum(entry['gen'] for key, entry in mix.items() if key in renewable_types)

    pct_renewable = renewable_mw / total_mw * 100 if total_mw else 0
    return pct_renewable

def generate_pie_chart(mix):
    labels = [key for key, entry in mix.items()]
    values = [entry['gen'] for entry in mix.values()]
    colors = plt.get_cmap('tab20').colors

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title("ERCOT Energy Mix")
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(IMAGE_FILE)
    plt.close()

def generate_pie_chart_legend(mix):
    labels = [key for key, entry in mix.items()]
    values = [entry['gen'] for entry in mix.values()]
    total = sum(values)
    colors = plt.get_cmap('tab20').colors

    # Create human-readable labels for legend: "Fuel: XX.X%"
    legend_labels = [f"{label}: {value / total * 100:.1f}%" for label, value in zip(labels, values)]

    plt.figure(figsize=(8, 6))  # Wider layout for legend
    wedges, _ = plt.pie(values, colors=colors, startangle=140)

    plt.title("ERCOT Energy Mix")
    plt.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5))
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(IMAGE_FILE, bbox_inches='tight')
    plt.close()

def post_to_twitter(text, image_path = None):
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY, TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
    )
    api = tweepy.API(auth)
    if image_path:
        media = api.media_upload(image_path)
        api.update_status(status=text, media_ids=[media.media_id])
    else:
        api.update_status(status=text)

def run():
    try:
        mix = fetch_fuel_mix()
        pct = calculate_renewables(mix)
        # generate_pie_chart_legend(mix)
        message = f"Currently ERCOT is running on {pct:.2f}% renewable energy. #Texas #ERCOT #Renewables"
        print("Posting to Twitter:", message)

        # post_to_twitter(message, IMAGE_FILE)
        post_to_twitter(message)

    except Exception:
        traceback.print_exc()

# ==== SCHEDULER ====
if __name__ == "__main__":
    run()  # Run immediately
    schedule.every(2).hours.at(":00").do(run)

    print("Bot running. Will post every 2 hours.")
    while True:
        schedule.run_pending()
        time.sleep(1)