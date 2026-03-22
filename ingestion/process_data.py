import pandas as pd
import requests
import io
from pathlib import Path

# ------------------
# Paths
# ------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_PATH = BASE_DIR / "data" / "processed"
PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

# ------------------
# Download raw data from GitHub
# ------------------
BASE_URL = "https://raw.githubusercontent.com/BetsySnchzB/DatasetsP/refs/heads/main/"

def load_csv(filename, **kwargs):
    url = BASE_URL + filename
    response = requests.get(url)
    return pd.read_csv(io.StringIO(response.text), **kwargs)

print("Downloading data...")

income_zip     = load_csv("IncomeByZip.csv")
pop_per_zip    = load_csv("PopulationByZip.csv")
fire_station   = load_csv("Fire_Station.csv")
police_station = load_csv("PoliceStation_gdb_-1134624143014171098.csv")
private_school = load_csv("Private_School.csv")
public_school  = load_csv("SchoolSite_gdb_-5745748764799769002.csv")
park_facility  = load_csv("Park_Facility.csv")
hotel          = load_csv("HotelMotelInn_gdb_-4704617087620911628.csv")

print("Download complete!")

# ------------------
# Clean ZIP codes helper
# ------------------
def clean_zip(df, col):
    df[col] = df[col].astype(str).str.extract(r'(\d{5})')[0].str.zfill(5)
    return df

# ------------------
# Clean income & population
# ------------------
income_zip = clean_zip(income_zip, "ZIP Code")
income_zip["INCOME"] = income_zip["Value"].str.replace(",", "").str.strip().astype(float)
income_zip = income_zip[["ZIP Code", "INCOME"]].rename(columns={"ZIP Code": "ZIP"})

pop_per_zip = clean_zip(pop_per_zip, "ZIP Code")
pop_per_zip["Population"] = pop_per_zip["Value"].str.replace(",", "").str.strip().astype(float)
pop_per_zip = pop_per_zip[["ZIP Code", "Population"]].rename(columns={"ZIP Code": "ZIP"})

# ------------------
# Clean facility datasets
# ------------------
def clean_facility(df, zip_col, name_col, lat_col, lon_col, facility_type):
    df = df[[zip_col, name_col, lat_col, lon_col]].copy()
    df.columns = ["ZIP", "NAME", "latitude", "longitude"]
    df = clean_zip(df, "ZIP")
    df["FACILITY_TYPE"] = facility_type
    return df.dropna(subset=["ZIP"])

fire_clean    = clean_facility(fire_station,   "ZIPCODE", "NAME", "LAT", "LON",   "Fire Station")
police_clean  = clean_facility(police_station, "ZIPCODE", "NAME", "LAT", "LON",   "Police Station")
private_clean = clean_facility(private_school, "ZIPCODE", "NAME", "LAT", "LON",   "Private School")
public_clean  = clean_facility(public_school,  "ZIPCODE", "NAME", "LAT", "LON",   "Public School")
park_clean    = clean_facility(park_facility,  "ZIPCODE", "NAME", "LAT", "LON",   "Park")
hotel_clean   = clean_facility(hotel,          "ZIPCODE", "NAME", "LAT", "LON",   "Hotel/Motel")

# ------------------
# Build facilities_points.csv
# ------------------
facilities_points = pd.concat(
    [fire_clean, police_clean, private_clean, public_clean, park_clean, hotel_clean],
    ignore_index=True
)

# ------------------
# Build zip_summary.csv
# ------------------
def count_facilities(df, col_name):
    return df.groupby("ZIP").size().reset_index(name=col_name)

zip_summary = income_zip.merge(pop_per_zip, on="ZIP", how="outer")

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
zip_summary["WEIGHTED_RATING"] = pd.cut(
    score,
    bins=[-1, score.quantile(0.33), score.quantile(0.66), float("inf")],
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