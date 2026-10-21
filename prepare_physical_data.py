
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SOURCE_FILE = ROOT / "data" / "physical_parameters.csv"
OUTPUT_FILE = ROOT / "data" / "physical_parameters_app.csv"

# Read the complete original dataset
df = pd.read_csv(SOURCE_FILE)

# Convert CPCB columns into application columns
app_df = pd.DataFrame({
    "record_id": df["SlNo"],
    "sample_date": pd.to_datetime(
        df["Data Acquisition Time"],
        format="%d-%m-%Y %H:%M",
        errors="coerce"
    ).dt.strftime("%Y-%m-%d"),
    "location": (
        df["Station"].fillna("").astype(str) + ", " +
        df["District"].fillna("").astype(str) + ", " +
        df["State"].fillna("").astype(str)
    ),
    "temperature_c": pd.to_numeric(
        df["Temperature (ºC)"], errors="coerce"
    ),
    "ph": float("nan"),
    "turbidity_ntu": pd.to_numeric(
        df["Turbidity (NTU)"], errors="coerce"
    ),
    "conductivity_us_cm": pd.to_numeric(
        df["Electric Conductivity (μS/cm)"], errors="coerce"
    ),
    "tds_mg_l": float("nan"),
    "dissolved_oxygen_mg_l": float("nan")
})

# Save all records
app_df.to_csv(OUTPUT_FILE, index=False)

print("Conversion completed!")
print("Original records:", len(df))
print("Converted records:", len(app_df))
print("Output:", OUTPUT_FILE)
