import pandas as pd
from pathlib import Path

# project directories
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def load_raw_datasets():
    """Load all raw datasets"""

    fire = pd.read_csv(RAW_DIR / "Fire_Station.csv")
    hospital = pd.read_csv(RAW_DIR / "Hospitalpoly_gdb_2921453914923425143.csv")
    hotel = pd.read_csv(RAW_DIR / "HotelMotelInn_gdb__4704617087620911628.csv")
    parks = pd.read_csv(RAW_DIR / "Park_Facility.csv")
    police = pd.read_csv(RAW_DIR / "PoliceStation_gdb__1134624143014717098.csv")
    private_school = pd.read_csv(RAW_DIR / "Private_School.csv")
    school = pd.read_csv(RAW_DIR / "SchoolSite_gdb__5745748764799769002.csv")

    population = pd.read_csv(RAW_DIR / "PopulationByZip.csv")
    income = pd.read_csv(RAW_DIR / "IncomeByZip.csv")

    return {
        "fire": fire,
        "hospital": hospital,
        "hotel": hotel,
        "parks": parks,
        "police": police,
        "private_school": private_school,
        "school": school,
        "population": population,
        "income": income,
    }


def run_pipeline():
    """Main pipeline execution"""

    data = load_raw_datasets()

    print("Datasets loaded successfully")

    for name, df in data.items():
        print(f"{name}: {len(df)} rows")


if __name__ == "__main__":
    run_pipeline()
