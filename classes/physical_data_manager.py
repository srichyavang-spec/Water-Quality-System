
import os
import tempfile
from pathlib import Path

import pandas as pd


class PhysicalDataManager:
    COLUMNS = [
        "record_id",
        "sample_date",
        "location",
        "temperature_c",
        "ph",
        "turbidity_ntu",
        "conductivity_us_cm",
        "tds_mg_l",
        "dissolved_oxygen_mg_l"
    ]

    NUMERIC_COLUMNS = [
        "temperature_c",
        "ph",
        "turbidity_ntu",
        "conductivity_us_cm",
        "tds_mg_l",
        "dissolved_oxygen_mg_l"
    ]

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def read_data(self):
        if not self.file_path.exists():
            empty_df = pd.DataFrame(columns=self.COLUMNS)
            self.write_data(empty_df)
            return empty_df

        try:
            df = pd.read_csv(self.file_path)

            missing = set(self.COLUMNS) - set(df.columns)
            if missing:
                raise ValueError(
                    f"Missing CSV columns: {', '.join(sorted(missing))}"
                )

            df = df[self.COLUMNS].copy()

            df["record_id"] = pd.to_numeric(
                df["record_id"], errors="coerce"
            )

            for column in self.NUMERIC_COLUMNS:
                df[column] = pd.to_numeric(
                    df[column], errors="coerce"
                )

            df["sample_date"] = pd.to_datetime(
                df["sample_date"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            df["location"] = df["location"].fillna("").astype(str)

            return df

        except (OSError, ValueError, pd.errors.EmptyDataError) as error:
            raise ValueError(f"Could not read CSV: {error}") from error

    def write_data(self, df):
        temp_path = None

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".csv",
                prefix="physical_",
                dir=self.file_path.parent,
                encoding="utf-8",
                newline="",
                delete=False
            ) as temp_file:
                temp_path = temp_file.name
                df[self.COLUMNS].to_csv(temp_file, index=False)

            os.replace(temp_path, self.file_path)
            temp_path = None

        except (OSError, ValueError, KeyError) as error:
            raise ValueError(f"Could not save CSV: {error}") from error

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def create_record(self, record):
        df = self.read_data()

        if df["record_id"].eq(record["record_id"]).any():
            raise ValueError("This record ID already exists.")

        updated = pd.concat(
            [df, pd.DataFrame([record], columns=self.COLUMNS)],
            ignore_index=True
        )

        self.write_data(updated)
        return updated

    def update_record(self, record_id, changes):
        df = self.read_data()
        matches = df["record_id"].eq(record_id)

        if not matches.any():
            raise ValueError("Record ID not found.")

        for column, value in changes.items():
            if column in self.COLUMNS and column != "record_id":
                df.loc[matches, column] = value

        self.write_data(df)
        return df

    def delete_record(self, record_id):
        df = self.read_data()
        matches = df["record_id"].eq(record_id)

        if not matches.any():
            raise ValueError("Record ID not found.")

        updated = df.loc[~matches].copy()
        self.write_data(updated)
        return updated
