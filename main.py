import traceback

from ercot.fuel_mix import FuelMix

def run():
    try:
        with FuelMix() as fuel_mix:
            message = f"Currently ERCOT is running on {fuel_mix.pct_renewable:.2f}% renewable energy. #Texas #ERCOT #Renewables"
            print("Posting to Twitter:", message)

    except Exception:
        traceback.print_exc()

# ==== SCHEDULER ====
if __name__ == "__main__":
    run()  # Run immediately
    # schedule.every(2).hours.at(":00").do(run)
    #
    # print("Bot running. Will post every 2 hours.")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)