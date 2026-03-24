import requests
import time
import pandas as pd

def geocode_address(address, city="Miami", state="FL"):
    """
    Converts a street address to lat/lon using OpenStreetMap Nominatim API.
    Free, no API key needed!
    """
    full_address = f"{address}, {city}, {state}, USA"
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": full_address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "know-your-zip-app"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding error for {address}: {e}")
    
    return None, None


def fill_missing_coordinates(df, address_col="ADDRESS", zip_col="ZIP"):
    """
    Takes a facilities dataframe and fills in missing lat/lon
    by geocoding addresses.
    """
    missing = df[df["latitude"].isna() | df["longitude"].isna()].copy()
    
    if missing.empty:
        print("No missing coordinates!")
        return df

    print(f"Geocoding {len(missing)} facilities with missing coordinates...")

    for idx, row in missing.iterrows():
        address = row.get(address_col, "")
        zip_code = row.get(zip_col, "")
        
        if not address:
            continue

        lat, lon = geocode_address(address)
        
        if lat and lon:
            df.at[idx, "latitude"] = lat
            df.at[idx, "longitude"] = lon

        # Be polite to the API — wait 1 second between requests
        time.sleep(1)

    filled = df[df["latitude"].notna()].shape[0]
    print(f"Done! {filled} facilities now have coordinates.")
    return df


if __name__ == "__main__":
    # Quick test
    lat, lon = geocode_address("10850 SW 211TH ST")
    print(f"Test result: {lat}, {lon}")