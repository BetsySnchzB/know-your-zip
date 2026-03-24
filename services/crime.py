import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FBI_API_KEY")
BASE_URL = "https://api.usa.gov/crime/fbi/sapi"

def get_crime_by_state(state_abbr="FL", year=2022):
    """
    Fetches crime data for a given state from the FBI Crime Data API.
    Returns a summary of crime statistics.
    """
    print(f"Fetching crime data for {state_abbr}...")

    url = f"{BASE_URL}/api/summarized/state/{state_abbr}/violent-crime/{year}/{year}"
    params = {"API_KEY": API_KEY}

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if "results" not in data or not data["results"]:
            print("No crime data found.")
            return None

        result = data["results"][0]

        summary = {
            "state": state_abbr,
            "year": year,
            "violent_crime": result.get("violent_crime", 0),
            "homicide": result.get("homicide", 0),
            "rape": result.get("rape_legacy", 0),
            "robbery": result.get("robbery", 0),
            "aggravated_assault": result.get("aggravated_assault", 0),
            "population": result.get("population", 0),
        }

        # Calculate crime rate per 100,000 people
        if summary["population"] > 0:
            summary["violent_crime_rate"] = round(
                (summary["violent_crime"] / summary["population"]) * 100000, 1
            )
        else:
            summary["violent_crime_rate"] = 0

        print(f"Crime data fetched! Violent crime rate: {summary['violent_crime_rate']} per 100k")
        return summary

    except Exception as e:
        print(f"Crime API error: {e}")
        return None


if __name__ == "__main__":
    data = get_crime_by_state("FL", 2022)
    if data:
        print(data)