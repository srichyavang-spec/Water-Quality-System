
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ---------------- 1. SETUP ----------------

st.set_page_config(page_title="Chemical Parameters", page_icon="🧪",
                   layout="wide")

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "chemical_parameters.csv"
REPORT_FOLDER = ROOT / "reports"

REPORT_FOLDER.mkdir(exist_ok=True)

st.title("🧪 Water Conditions Analysis")
st.write("Chemical water-quality analysis using CPCB data.")

# ---------------- 2. HELPER FUNCTIONS ----------------

def clean_data(df):
    """Clean headers and convert common missing markers to NaN."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Remove unnecessary unnamed columns
    df = df.loc[:, [
        not c.lower().startswith("unnamed") for c in df.columns
    ]]

    # Remove extra spaces
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    # Handle common missing-value markers
    df.replace(
        ["", "NA", "N/A", "NULL", "null", "None", "-", "--"],
        np.nan,
        inplace=True
    )

    # Add an ID column if the source does not have one
    if "Record_ID" not in df.columns:
        df.insert(
            0, "Record_ID",
            [f"CHEM-{i:06d}" for i in range(1, len(df) + 1)]
        )

    return df


def number_values(series):
    """Convert measurement values to numbers for analysis."""
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )


def find_column(df, words):
    """Find a column using its name."""
    for col in df.columns:
        name = "".join(ch for ch in col.lower() if ch.isalnum())
        if any(word in name for word in words):
            return col
    return None


def save_data(df):
    """Save CSV without an extra index column."""
    if df["Record_ID"].duplicated().any():
        raise ValueError("Record IDs must be unique.")

    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


def next_id(df):
    """Generate a new unique record ID."""
    used = set(df["Record_ID"].astype(str))
    number = 1

    while f"CHEM-{number:06d}" in used:
        number += 1

    return f"CHEM-{number:06d}"


# ---------------- 3. LOAD CSV ----------------

try:
    data = pd.read_csv(CSV_FILE, low_memory=False)
except FileNotFoundError:
    st.error(
        "Chemical CSV not found. Save the real CPCB dataset as "
        "data/chemical_parameters.csv."
    )
    st.stop()
except Exception as error:
    st.error(f"Could not read the CSV: {error}")
    st.stop()

data = clean_data(data)

# Identify location and date columns
state_col = find_column(data, ["state"])
district_col = find_column(data, ["district"])
river_col = find_column(data, ["river"])
station_col = find_column(data, ["station"])
date_col = find_column(
    data, ["dataacquisitiontime", "samplingdate", "sampledate", "date"]
)

# Identify numeric chemical measurement columns
metadata_words = [
    "recordid", "state", "district", "station", "river",
    "latitude", "longitude", "date", "time", "year",
    "location", "agency", "sample", "monitoring", "serial",
    "slno", "village", "tehsil", "block", "basin", "region",
    "sitecode", "stationcode", "pincode"
]

parameters = []

for col in data.columns:
    name = "".join(ch for ch in col.lower() if ch.isalnum())

    if name == "id" or any(word in name for word in metadata_words):
        continue

    if number_values(data[col]).notna().any():
        parameters.append(col)

if not parameters:
    st.error("No numeric chemical measurement columns were found.")
    st.stop()

# ---------------- 4. SEARCH AND FILTER ----------------

st.header("Search and Filter")

filtered = data.copy()
search = st.text_input("Search records")

# Filter using available location columns
for label, col in [
    ("State", state_col),
    ("District", district_col),
    ("River", river_col)
]:
    if col:
        options = sorted(data[col].dropna().astype(str).unique())
        selected = st.selectbox(label, ["All"] + options)

        if selected != "All":
            filtered = filtered[filtered[col].astype(str) == selected]

# Search across all columns
if search.strip():
    matches = filtered.astype(str).apply(
        lambda col: col.str.contains(
            search.strip(), case=False, regex=False, na=False
        )
    ).any(axis=1)

    filtered = filtered[matches]

sort_col = st.selectbox("Sort records by", list(filtered.columns))
descending = st.checkbox("Descending order")

filtered = filtered.sort_values(
    sort_col, ascending=not descending, na_position="last"
)

st.caption(f"Showing {len(filtered)} of {len(data)} records.")
st.dataframe(filtered, use_container_width=True, hide_index=True)

# ---------------- 5. STATISTICS ----------------

st.header("Summary Statistics")

col1, col2, col3 = st.columns(3)
col1.metric("Records", len(filtered))
col2.metric("Stations", filtered[station_col].nunique()
            if station_col else "Not available")
col3.metric("Missing cells", int(filtered.isna().sum().sum()))

stats = []

for parameter in parameters:
    values = number_values(filtered[parameter])
    valid = values.dropna()

    stats.append({
        "Parameter": parameter,
        "Valid values": valid.count(),
        "Missing/non-numeric": values.isna().sum(),
        "Mean": round(valid.mean(), 3) if len(valid) else np.nan,
        "Median": round(valid.median(), 3) if len(valid) else np.nan,
        "Minimum": round(valid.min(), 3) if len(valid) else np.nan,
        "Maximum": round(valid.max(), 3) if len(valid) else np.nan
    })

stats_df = pd.DataFrame(stats)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

# ---------------- 6. VISUALIZATION ----------------

st.header("Charts")

parameter = st.selectbox("Choose chemical parameter", parameters)

group_columns = [
    c for c in [station_col, river_col, district_col, state_col] if c
]

chart1, chart2 = st.columns(2)

# Bar chart: average measurement by location
with chart1:
    st.subheader("Bar Chart")

    if group_columns:
        group = st.selectbox("Group by", group_columns)

        chart_data = pd.DataFrame({
            "Location": filtered[group].fillna("Unknown").astype(str),
            "Value": number_values(filtered[parameter])
        }).dropna(subset=["Value"])

        averages = chart_data.groupby("Location")["Value"].mean()
        averages = averages.sort_values(ascending=False).head(20)

        if not averages.empty:
            st.bar_chart(averages)
        else:
            st.info("No numeric values available.")
    else:
        st.info("No location column is available.")

# Line chart: average measurement over time
with chart2:
    st.subheader("Line Chart")

    if date_col:
        chart_data = pd.DataFrame({
            "Date": pd.to_datetime(
                filtered[date_col], errors="coerce", dayfirst=True
            ),
            "Value": number_values(filtered[parameter])
        }).dropna()

        if not chart_data.empty:
            trend = chart_data.groupby("Date")["Value"].mean().sort_index()
            st.line_chart(trend)
        else:
            st.info("No valid date and measurement pairs.")
    else:
        st.info("No date column was found for a time-trend chart.")

# ---------------- 7. REPORT EXPORT ----------------

st.header("Export Report")

report = (
    "WATER QUALITY SYSTEM - CHEMICAL PARAMETERS\n"
    f"Generated: {datetime.now()}\n"
    f"Total records: {len(data)}\n"
    f"Filtered records: {len(filtered)}\n"
    f"Missing cells: {int(filtered.isna().sum().sum())}\n\n"
    + stats_df.to_string(index=False)
)

st.download_button(
    "Download Summary Report",
    report,
    file_name="chemical_parameters_report.txt",
    mime="text/plain"
)

st.download_button(
    "Download Filtered CSV",
    filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="chemical_parameters_filtered.csv",
    mime="text/csv"
)

if st.button("Save Report in reports folder"):
    filename = "chemical_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
    (REPORT_FOLDER / filename).write_text(report, encoding="utf-8")
    st.success("Report saved.")

# ---------------- 8. CRUD OPERATIONS ----------------

st.header("Manage Records")

add_tab, edit_tab, delete_tab = st.tabs(["Add", "Edit", "Delete"])

# ADD
with add_tab:
    with st.form("add_record"):
        entered = {}

        # Enter available station and location details
        info_columns = list(dict.fromkeys(
            c for c in [state_col, district_col, river_col,
                        station_col, date_col] if c
        ))

        for col in info_columns:
            entered[col] = st.text_input(col)

        new_parameter = st.selectbox(
            "Measurement parameter", parameters, key="add_parameter"
        )
        new_value = st.text_input("Measurement value")

        add_clicked = st.form_submit_button("Add Record")

    if add_clicked:
        try:
            if not new_value.strip():
                raise ValueError("Measurement value is required.")

            measurement = float(new_value)

            if not np.isfinite(measurement):
                raise ValueError("Enter a valid finite number.")

            if station_col and not entered.get(station_col, "").strip():
                raise ValueError("Station information is required.")

            if date_col:
                date_text = entered.get(date_col, "").strip()

                if not date_text or pd.isna(pd.to_datetime(
                    date_text, errors="coerce", dayfirst=True
                )):
                    raise ValueError("Enter a valid date.")

            record = {col: np.nan for col in data.columns}
            record["Record_ID"] = next_id(data)

            for col, value in entered.items():
                if value.strip():
                    record[col] = value.strip()

            record[new_parameter] = measurement

            updated = pd.concat(
                [data, pd.DataFrame([record])], ignore_index=True
            )

            save_data(updated)
            st.success("Record added.")
            st.rerun()

        except (ValueError, OSError) as error:
            st.error(str(error))

# EDIT
with edit_tab:
    if data.empty:
        st.info("No records to edit.")
    else:
        record_id = st.selectbox(
            "Select Record ID",
            data["Record_ID"].astype(str).tolist(),
            key="edit_id"
        )

        fields = [c for c in data.columns if c != "Record_ID"]
        field = st.selectbox("Field to edit", fields)
        old_value = data.loc[
            data["Record_ID"].astype(str) == record_id, field
        ].iloc[0]

        with st.form("edit_record"):
            new_text = st.text_input(
                "New value",
                value="" if pd.isna(old_value) else str(old_value)
            )
            edit_clicked = st.form_submit_button("Save Changes")

        if edit_clicked:
            try:
                if new_text.strip() == "":
                    value = np.nan
                elif field in parameters or pd.api.types.is_numeric_dtype(
                    data[field]
                ):
                    value = float(new_text)

                    if not np.isfinite(value):
                        raise ValueError("Enter a valid finite number.")
                else:
                    value = new_text.strip()

                if field == date_col and pd.isna(pd.to_datetime(
                    value, errors="coerce", dayfirst=True
                )):
                    raise ValueError("Enter a valid date.")

                updated = data.copy()
                updated[field] = updated[field].astype("object")
                updated.loc[
                    updated["Record_ID"].astype(str) == record_id, field
                ] = value

                save_data(updated)
                st.success("Record updated.")
                st.rerun()

            except (ValueError, OSError) as error:
                st.error(str(error))

# DELETE
with delete_tab:
    if data.empty:
        st.info("No records to delete.")
    else:
        record_id = st.selectbox(
            "Record ID to delete",
            data["Record_ID"].astype(str).tolist(),
            key="delete_id"
        )

        confirm = st.checkbox("Confirm deletion")

        if st.button("Delete Record"):
            if not confirm:
                st.warning("Please confirm before deleting.")
            else:
                updated = data[
                    data["Record_ID"].astype(str) != record_id
                ].copy()

                try:
                    save_data(updated)
                    st.success("Record deleted.")
                    st.rerun()
                except (ValueError, OSError) as error:
                    st.error(str(error))