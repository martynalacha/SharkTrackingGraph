import os
import re

import pandas as pd


def parse_weight(value):
    """
    Parses weight: removes commas, '+', and units.
    Converts lb to kg. Returns None if value is missing.
    """
    if pd.isna(value):
        return None

    cleaned = str(value).strip().replace(",", "")
    match = re.search(r"\d+\.?\d*", cleaned)
    if not match:
        return None

    try:
        val = float(match.group())
        return round(val * 0.453592, 2) if "lb" in str(value).lower() else val
    except ValueError:
        return None


def parse_length(value):
    """
    Parses formats like '5 ft 4 in.', '4 ft 11.5 in.', '1.5 m' to meters.
    Handles extra spaces, dots, and punctuation.
    """
    if pd.isna(value):
        return None

    s = str(value).lower()
    s = s.replace(",", " ").replace('"', "").replace("'", "")
    s = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    ft = re.search(r"(\d+(?:\.\d+)?)\s*ft", s)
    inc = re.search(r"(\d+(?:\.\d+)?)\s*in", s)

    total_inches = 0
    if ft:
        total_inches += float(ft.group(1)) * 12
    if inc:
        total_inches += float(inc.group(1))

    if total_inches > 0:
        return round(total_inches * 0.0254, 2)

    m_match = re.search(r"(\d+(?:\.\d+)?)\s*m", s)
    if m_match:
        return float(m_match.group(1))

    return None


def clean_csv_data(input_file_path: str, output_file_path: str):
    """
    Loads, analyzes, cleans duplicates, and handles missing values in the telemetry CSV data.
    """

    if not os.path.exists(input_file_path):
        print(f"Error: Source file not found at {input_file_path}")
        return

    df = pd.read_csv(input_file_path)
    initial_row_count = len(df)
    print(f"Initial row count: {initial_row_count}")

    print("\n--Missing Values Analysis--")
    print(df.isnull().sum())

    critical_columns = ["id", "datetime", "latitude", "longitude"]

    df.dropna(subset=critical_columns, how="any", inplace=True)
    dropped_rows = initial_row_count - len(df)
    print(f"Removed {dropped_rows} rows with missing values. Remaining row count: {len(df)}")

    duplicate_mask = df.duplicated(subset=["id", "datetime", "latitude", "longitude"], keep="first")
    duplicate_count = duplicate_mask.sum()
    print("\n--Duplicate Analysis--")
    print(f"Found {duplicate_count} exact telemetry duplicates.")

    if duplicate_count > 0:
        df.drop_duplicates(subset=["id", "datetime", "latitude", "longitude"], keep="first", inplace=True)
        print(f"Row count after removing duplicates: {len(df)}")

    print("\n--Applying unit conversions and cleaning numeric data--")
    df["weight"] = df["weight"].apply(parse_weight)
    df["length"] = df["length"].apply(parse_length)

    print("\n--Data Analysis--")
    unique_sharks_count = df["id"].nunique()
    unique_species_count = df["species"].nunique()
    print(f"Total unique sharks (by ID): {unique_sharks_count}")
    print(f"Total unique species: {unique_species_count}")

    species_distribution = df.groupby("species")["id"].nunique()
    print(species_distribution.to_string())

    df["datetime"] = df["datetime"].astype(str)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df.to_csv(output_file_path, index=False)
    print(f"\nCleaned dataset saved to {output_file_path}")


if __name__ == "__main__":
    # Local execution paths for testing
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_path = os.path.join(base_dir, "data", "sharks.csv")
    output_path = os.path.join(base_dir, "data", "sharks_data_clean.csv")
    clean_csv_data(input_path, output_path)
