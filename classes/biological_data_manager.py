
from pathlib import Path
import os
import tempfile

import pandas as pd


class BiologicalDataManager:
    """Manage biological water-quality records stored in a CSV file."""

    REQUIRED_COLUMNS = [
        "SlNo",
        "Station",
        "Agency",
        "State LGD Code",
        "State",
        "District LGD Code",
        "District",
        "Tehsil",
        "Block",
        "Village",
        "River",
        "Basin",
        "Tributary",
        "Subtributary",
        "SubSubtributary",
        "Local River",
        "Latitude",
        "Longitude",
        "Data Acquisition Time",
        "Biochemical Oxygen Demand (mg/L)",
        "Chemical Oxygen Demand (mg/L)",
        "Fecal Coliform (MPN/100mL)",
        "Total Coliform (MPN/100mL)",
    ]

    def __init__(self, file_path="data/biological_parameters.csv"):
        self.file_path = Path(file_path)

    def load_data(self):
        """Read the CSV and report errors without crashing the app."""
        data = pd.DataFrame()

        try:
            data = pd.read_csv(self.file_path)

            missing_columns = [
                col for col in self.REQUIRED_COLUMNS
                if col not in data.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Dataset is missing columns: {missing_columns}"
                )

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Dataset not found: {self.file_path}"
            )

        except (pd.errors.ParserError, UnicodeDecodeError) as error:
            raise ValueError(f"Could not read the CSV: {error}") from error

        except OSError as error:
            raise OSError(f"Could not access the CSV: {error}") from error

        else:
            return data

        finally:
            # Runs whether reading succeeds or fails.
            pass

    def save_data(self, data):
        """Save safely using a temporary file and atomic replacement."""
        temp_path = None

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                suffix=".csv",
                prefix="biological_tmp_",
                dir=self.file_path.parent,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                data.to_csv(temp_file, index=False)

            os.replace(temp_path, self.file_path)

        except (OSError, PermissionError) as error:
            raise OSError(f"Could not save the dataset: {error}") from error

        finally:
            # Remove an unfinished temporary file if one remains.
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def add_record(self, record):
        """Add a record after checking its ID and duplicate key."""
        data = self.load_data()
        new_record = pd.DataFrame([record])

        missing = [
            col for col in data.columns
            if col not in new_record.columns
        ]
        extra = [
            col for col in new_record.columns
            if col not in data.columns
        ]

        if missing or extra:
            raise ValueError(
                f"Record columns do not match. "
                f"Missing: {missing}; extra: {extra}"
            )

        new_id = new_record.iloc[0]["SlNo"]

        if pd.isna(new_id) or str(new_id).strip() == "":
            raise ValueError("SlNo must not be empty.")

        if data["SlNo"].astype(str).eq(str(new_id)).any():
            raise ValueError(f"SlNo {new_id} already exists.")

        station = str(new_record.iloc[0]["Station"]).strip()
        timestamp = str(
            new_record.iloc[0]["Data Acquisition Time"]
        ).strip()

        duplicate = (
            data["Station"].astype(str).str.strip().eq(station)
            & data["Data Acquisition Time"].astype(str)
            .str.strip().eq(timestamp)
        )

        if duplicate.any():
            raise ValueError(
                "A record already exists for this station and time."
            )

        updated = pd.concat([data, new_record], ignore_index=True)
        self.save_data(updated)

    def update_record(self, record_id, changes):
        """Update an existing record identified by SlNo."""
        data = self.load_data()
        matches = data["SlNo"].astype(str).eq(str(record_id))

        if matches.sum() == 0:
            raise ValueError(f"Record ID {record_id} was not found.")

        if matches.sum() > 1:
            raise ValueError(f"Record ID {record_id} is not unique.")

        protected = {"SlNo"}
        unknown = set(changes) - set(data.columns)

        if unknown:
            raise ValueError(f"Unknown columns: {sorted(unknown)}")

        if protected.intersection(changes):
            raise ValueError("SlNo cannot be changed.")

        for column, value in changes.items():
            data.loc[matches, column] = value

        self.save_data(data)

    def delete_record(self, record_id):
        """Delete a record only if its ID uniquely identifies it."""
        data = self.load_data()
        matches = data["SlNo"].astype(str).eq(str(record_id))

        if matches.sum() == 0:
            raise ValueError(f"Record ID {record_id} was not found.")

        if matches.sum() > 1:
            raise ValueError(f"Record ID {record_id} is not unique.")

        updated = data.loc[~matches].copy()
        self.save_data(updated)
