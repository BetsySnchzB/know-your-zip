import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CENSUS_API_KEY")

def get_census_data():
    """
    Fetches live demographic data from the US Census Bureau API.
    Returns a DataFrame with one row per ZIP code.
    """

    print("Fetching Census data...")

    # Census variable codes:
    # B19013_001E = Median household income
    # B01003_001E = Total population
    # B15003_022E = Bachelor's degree count
    # B01002_001E = Median age

    variables = "B19013_001E,B01003_001E,B15003_022E,B01002_001E"

    url = (
        f"https://api.census.gov/data/2022/acs/acs5"
        f"?get=NAME,{variables}"
        f"&for=zip%20code%20tabulation%20area:*"
        f"&key={API_KEY}"
    )

    response = requests.get(url)

    if response.status_code != 200:
        print(f"Census API error: {response.status_code}")
        return None

    data = response.json()

    # First row is headers
    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    # Rename columns to friendly names
    df = df.rename(columns={
        "zip code tabulation area": "ZIP",
        "B19013_001E": "INCOME",
        "B01003_001E": "Population",
        "B15003_022E": "BACHELORS_DEGREE",
        "B01002_001E": "MEDIAN_AGE",
    })

    # Clean up
    df["ZIP"] = df["ZIP"].astype(str).str.zfill(5)

    for col in ["INCOME", "Population", "BACHELORS_DEGREE", "MEDIAN_AGE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove ZIPs with no income data
    df = df[df["INCOME"] > 0]

    # Keep only relevant columns
    df = df[["ZIP", "INCOME", "Population", "BACHELORS_DEGREE", "MEDIAN_AGE"]]

    print(f"Census data fetched! {len(df)} ZIP codes found.")
    return df


if __name__ == "__main__":
    df = get_census_data()
    if df is not None:
        print(df.head())