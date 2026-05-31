import os

import pandas as pd


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
