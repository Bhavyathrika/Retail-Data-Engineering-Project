
import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    r"C:\Users\nihar\Downloads\data_engineering_sample_data"
)

FILES = {
    "customers": DATA_PATH / "customers_source.csv",
    "orders": DATA_PATH / "orders_source.csv"
}


def profile_dataset(name, file_path):
    df = pd.read_csv(file_path)

    print(f"\n{'=' * 50}")
    print(f"DATA PROFILE: {name.upper()}")
    print(f"{'=' * 50}")

    print("Total rows:", len(df))
    print("Total columns:", len(df.columns))

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:", df.duplicated().sum())

    print("\nUnique values:")
    print(df.nunique())

    print("\nStatistical summary:")
    print(df.describe(include="all").to_string())

    report_path = Path("reports")
    report_path.mkdir(exist_ok=True)

    df.describe(include="all").to_csv(
        report_path / f"{name}_profile.csv"
    )

    df.isnull().sum().to_csv(
        report_path / f"{name}_missing_values.csv"
    )

    print(f"\nReports saved for {name}.")


if __name__ == "__main__":
    for name, file_path in FILES.items():
        profile_dataset(name, file_path)
