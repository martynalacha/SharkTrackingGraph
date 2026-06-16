import os

import pandas as pd


def generate_qa_report(raw_path: str, clean_path: str):
    """
    QA report comparing raw vs cleaned CSV data.
    """

    raw_df = pd.read_csv(raw_path)
    clean_df = pd.read_csv(clean_path)

    print("=" * 60)
    print("\n --- General Data Quality Report ---")
    print(f"Raw rows: {len(raw_df)}")
    print(f"Cleaned rows: {len(clean_df)}")

    print("\n--- Missing values (raw)")
    print(raw_df.isnull().sum())

    print("\n--- Missing balues (clean) ---")
    print(clean_df.isnull().sum())

    lat = pd.to_numeric(clean_df["latitude"], errors="coerce")
    lon = pd.to_numeric(clean_df["longitude"], errors="coerce")
    print("\n--- Cooridinate validity (clean) ---")
    print(f"Non-numeric/NaN latitude: {lat.isna().sum()}")
    print(f"Non-numeric/NaN longitude: {lon.isna().sum()}")
    print(f"Latitude out of [-90, 90]: {((lat < - 90) | (lat > 90)).sum()}")
    print(f"Longitude out of [-180, 180]: {((lon < -180) | (lon > 180)).sum()}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    raw_path = os.path.join(base_dir, "data", "sharks.csv")
    clean_path = os.path.join(base_dir, "data", "sharks_data_clean.csv")
    generate_qa_report(raw_path, clean_path)
