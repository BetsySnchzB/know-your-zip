import pandas as pd
import requests
import io
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.geocoding import fill_missing_coordinates

load_dotenv()

# ------------------
# Paths
# ------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_PATH = BASE_DIR / "data" / "processed"
PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

# ------------------
# Download facility CSVs from GitHub
# ------------------
BASE_URL = "https://raw.githubusercontent.com/BetsySnchzB/DatasetsP/refs/heads/main/"

def load_csv(filename, **kwargs):
    url = BASE_URL + filename
    response = requests.get(url)
    return pd.read_csv(io.StringIO(response.text), **kwargs)

print("Downloading facility data...")

fire_station   = load_csv("Fire_Station.csv")
police_station = load_csv("PoliceStation_gdb_-1134624143014171098.csv")
private_school = load_csv("Private_School.csv")
public_school  = load_csv("SchoolSite_gdb_-5745748764799769002.csv")
park_facility  = load_csv("Park_Facility.csv")
hotel          = load_csv("HotelMotelInn_gdb_-4704617087620911628.csv")

print("Facility data downloaded!")

# ------------------
# Fetch live demographic data from Census API
# ------------------
def get_census_data():
    print("Fetching live Census data...")
    API_KEY = os.getenv("CENSUS_API_KEY")
    variables = "B19013_001E,B01003_001E,B15003_022E,B01002_001E"
    url = (
        f"https://api.census.gov/data/2022/acs/acs5"
        f"?get=NAME,{variables}"
        f"&for=zip%20code%20tabulation%20area:*"
        f"&key={API_KEY}"
    )
    response = requests.get(url)
    data = response.json()
    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)
    df = df.rename(columns={
        "zip code tabulation area": "ZIP",
        "B19013_001E": "INCOME",
        "B01003_001E": "Population",
        "B15003_022E": "BACHELORS_DEGREE",
        "B01002_001E": "MEDIAN_AGE",
    })
    df["ZIP"] = df["ZIP"].astype(str).str.zfill(5)
    for col in ["INCOME", "Population", "BACHELORS_DEGREE", "MEDIAN_AGE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["INCOME"] > 0]
    print(f"Census data fetched! {len(df)} ZIP codes found.")
    return df[["ZIP", "INCOME", "Population", "BACHELORS_DEGREE", "MEDIAN_AGE"]]

demographics = get_census_data()

# ------------------
# Clean ZIP codes helper
# ------------------
def clean_zip(df, col):
    df[col] = df[col].astype(str).str.extract(r'(\d{5})')[0].str.zfill(5)
    return df

# ------------------
# Clean facility datasets
# ------------------
def clean_facility(df, zip_col, name_col, addr_col, lat_col, lon_col, facility_type):
    df = df[[zip_col, name_col, addr_col, lat_col, lon_col]].copy()
    df.columns = ["ZIP", "NAME", "ADDRESS", "latitude", "longitude"]
    df = clean_zip(df, "ZIP")
    df["FACILITY_TYPE"] = facility_type
    return df.dropna(subset=["ZIP"])

fire_clean    = clean_facility(fire_station,   "ZIPCODE", "NAME", "ADDRESS", "LAT", "LON", "Fire Station")
police_clean  = clean_facility(police_station, "ZIPCODE", "NAME", "ADDRESS", "LAT", "LON", "Police Station")
private_clean = clean_facility(private_school, "ZIPCODE", "NAME", "ADDRESS", "LAT", "LON", "Private School")
public_clean  = clean_facility(public_school,  "ZIPCODE", "NAME", "ADDRESS", "LAT", "LON", "Public School")
park_clean    = clean_facility(park_facility,  "ZIPCODE", "NAME", "ADDRESS", "LAT", "LON", "Park")
hotel_clean   = clean_facility(hotel,          "ZIPCODE", "NAME", "ADDRESS", "LAT", "LON", "Hotel/Motel")

# ------------------
# Build facilities_points.csv
# ------------------
facilities_points = pd.concat(
    [fire_clean, police_clean, private_clean, public_clean, park_clean, hotel_clean],
    ignore_index=True
)

facilities_points = fill_missing_coordinates(facilities_points)

# ------------------
# Build zip_summary.csv
# ------------------
def count_facilities(df, col_name):
    return df.groupby("ZIP").size().reset_index(name=col_name)

zip_summary = demographics.copy()

for df, col in [
    (fire_clean,    "FIRE_STATION_COUNT"),
    (police_clean,  "POLICE_STATION_COUNT"),
    (private_clean, "PRIVATE_SCHOOL_COUNT"),
    (public_clean,  "PUBLIC_SCHOOL_COUNT"),
    (park_clean,    "PARK_COUNT"),
    (hotel_clean,   "HOTEL_COUNT"),
]:
    zip_summary = zip_summary.merge(count_facilities(df, col), on="ZIP", how="left")

zip_summary = zip_summary.fillna(0)

# ------------------
# Weighted facility score
# ------------------
weights = {
    "FIRE_STATION_COUNT":   3,
    "POLICE_STATION_COUNT": 3,
    "PUBLIC_SCHOOL_COUNT":  2,
    "PRIVATE_SCHOOL_COUNT": 1,
    "PARK_COUNT":           2,
    "HOTEL_COUNT":          1,
}

zip_summary["FACILITY_SCORE_WEIGHTED"] = sum(
    zip_summary[col] * w for col, w in weights.items()
)

# ------------------
# Weighted rating (Low / Medium / High)
# ------------------
score = zip_summary["FACILITY_SCORE_WEIGHTED"]
zip_summary["WEIGHTED_RATING"] = pd.qcut(
    score.rank(method="first"),
    q=3,
    labels=["Low", "Medium", "High"]
)

# ------------------
# Save to processed/
# ------------------
zip_summary.to_csv(PROCESSED_PATH / "zip_summary.csv", index=False)
facilities_points.to_csv(PROCESSED_PATH / "facilities_points.csv", index=False)

print(f"zip_summary.csv saved — {zip_summary.shape[0]} ZIPs")
print(f"facilities_points.csv saved — {facilities_points.shape[0]} facilities")
print("Data processed successfully!")