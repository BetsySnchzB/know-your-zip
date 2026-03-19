from pathlib import Path
import pandas as pd

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Ensure processed folder exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def process_zip_summary():
    df = pd.read_csv(RAW_DIR / "zip_summary.csv")
    
    # Example cleaning
    df["ZIP"] = df["ZIP"].astype(str).str[:5].str.zfill(5)
    
    df.to_csv(PROCESSED_DIR / "zip_summary.csv", index=False)
    print("Processed zip_summary.csv")

def process_facilities():
    df = pd.read_csv(RAW_DIR / "facilities_points.csv")
    
    # Example cleaning (you can expand later)
    df["ZIP"] = df["ZIP"].astype(str).str[:5].str.zfill(5)
    
    df.to_csv(PROCESSED_DIR / "facilities_points.csv", index=False)
    print("Processed facilities_points.csv")

if __name__ == "__main__":
    process_zip_summary()
    process_facilities()
