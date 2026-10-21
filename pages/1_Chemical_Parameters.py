
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Chemical Parameters", page_icon="🧪", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "chemical_parameters.csv"
REPORT_FOLDER = ROOT / "reports"
REPORT_FOLDER.mkdir(exist_ok=True)

st.title("🧪 Water Conditions Analysis")
st.write("Chemical water-quality analysis using CPCB data.")


def clean_data(df):
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.lower().str.startswith("unnamed")]

    for col in df.select_dtypes(include="object"):
        df[col] = df[col].str.strip()

    df.replace(["", "NA", "N/A", "NULL", "null", "None", "-", "--"],
               np.nan, inplace=True)

    if "Record_ID" not in df:
        df.insert(0, "Record_ID",
                  [f"CHEM-{i:06d}" for i in range(1, len(df) + 1)])
    return df


def numbers(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )


def find_col(df, words):
    for col in df.columns:
        name = "".join(ch for ch in col.lower() if ch.isalnum())
        if any(word in name for word in words):
            return col
    return None


def save_data(df):
    if df["Record_ID"].duplicated().any():
        raise ValueError("Record IDs must be unique.")
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


def next_id(df):
    used = set(df["Record_ID"].astype(str))
    i = 1
    while f"CHEM-{i:06d}" in used:
        i += 1
    return f"CHEM-{i:06d}"


try:
    data = clean_data(pd.read_csv(CSV_FILE, low_memory=False))
except FileNotFoundError:
    st.error("Dataset not found: data/chemical_parameters.csv")
    st.stop()
except Exception as error:
    st.error(f"Could not read CSV: {error}")
    st.stop()

state_col = find_col(data, ["state"])
district_col = find_col(data, ["district"])
river_col = find_col(data, ["river"])
station_col = find_col(data, ["station"])
date_col = find_col(
    data, ["dataacquisitiontime", "samplingdate", "sampledate", "date"]
)

metadata = [
    "recordid", "state", "district", "station", "river", "latitude",
    "longitude", "date", "time", "year", "location", "agency", "sample",
    "monitoring", "serial", "slno", "village", "tehsil", "block", "basin",
    "region", "sitecode", "stationcode", "pincode"
]

parameters = []
for col in data.columns:
    name = "".join(ch for ch in col.lower() if ch.isalnum())
    if name != "id" and not any(word in name for word in metadata):
        if numbers(data[col]).notna().any():
            parameters.append(col)

if not parameters:
    st.error("No numeric chemical measurement columns were found.")
    st.stop()

st.header("Search and Filter")
filtered = data.copy()
search = st.text_input("Search records")

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

st.header("Summary Statistics")
c1, c2, c3 = st.columns(3)
c1.metric("Records", len(filtered))
c2.metric("Stations", filtered[station_col].nunique()
          if station_col else "Not available")
c3.metric("Missing cells", int(filtered.isna().sum().sum()))

stats = []
for parameter_name in parameters:
    values = numbers(filtered[parameter_name])
    valid = values.dropna()
    stats.append({
        "Parameter": parameter_name,
        "Valid values": valid.count(),
        "Missing/non-numeric": values.isna().sum(),
        "Mean": round(valid.mean(), 3) if len(valid) else np.nan,
        "Median": round(valid.median(), 3) if len(valid) else np.nan,
        "Minimum": round(valid.min(), 3) if len(valid) else np.nan,
        "Maximum": round(valid.max(), 3) if len(valid) else np.nan
    })

stats_df = pd.DataFrame(stats)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

st.header("Charts")
parameter = st.selectbox("Choose chemical parameter", parameters)
groups = [c for c in [station_col, river_col, district_col, state_col] if c]
left, right = st.columns(2)

with left:
    st.subheader("Bar Chart")
    if groups:
        group = st.selectbox("Group by", groups)
        chart_data = pd.DataFrame({
            "Location": filtered[group].fillna("Unknown").astype(str),
            "Value": numbers(filtered[parameter])
        }).dropna(subset=["Value"])

        averages = chart_data.groupby("Location")["Value"].mean()
        averages = averages.sort_values(ascending=False).head(20)

        if not averages.empty:
            st.bar_chart(averages)
        else:
            st.info("No numeric values available.")
    else:
        st.info("No location column is available.")

with right:
    st.subheader("Line Chart")
    if date_col:
        chart_data = pd.DataFrame({
            "Date": pd.to_datetime(
                filtered[date_col], errors="coerce", dayfirst=True
            ),
            "Value": numbers(filtered[parameter])
        }).dropna()

        if not chart_data.empty:
            trend = chart_data.groupby("Date")["Value"].mean().sort_index()
            st.line_chart(trend)
        else:
            st.info("No valid date and measurement pairs.")
    else:
        st.info("No date column was found.")

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
    "Download Summary Report", report,
    file_name="chemical_parameters_report.txt", mime="text/plain"
)
st.download_button(
    "Download Filtered CSV",
    filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="chemical_parameters_filtered.csv", mime="text/csv"
)

if st.button("Save Report in reports folder"):
    filename = "chemical_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
    (REPORT_FOLDER / filename).write_text(report, encoding="utf-8")
    st.success("Report saved.")

st.header("Manage Records")
add_tab, edit_tab, delete_tab = st.tabs(["Add", "Edit", "Delete"])

with add_tab:
    info_cols = list(dict.fromkeys(
        c for c in [state_col, district_col, river_col, station_col, date_col] if c
    ))

    with st.form("add_record"):
        entered = {col: st.text_input(col) for col in info_cols}
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
                raise ValueError("Enter a valid number.")

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
            record.update({
                col: value.strip()
                for col, value in entered.items() if value.strip()
            })
            record[new_parameter] = measurement

            updated = pd.concat(
                [data, pd.DataFrame([record])], ignore_index=True
            )
            save_data(updated)
            st.success("Record added.")
            st.rerun()

        except (ValueError, OSError) as error:
            st.error(str(error))

with edit_tab:
    if data.empty:
        st.info("No records to edit.")
    else:
        record_id = st.selectbox(
            "Select Record ID", data["Record_ID"].astype(str).tolist(),
            key="edit_id"
        )
        field = st.selectbox(
            "Field to edit", [c for c in data.columns if c != "Record_ID"]
        )
        old_value = data.loc[
            data["Record_ID"].astype(str) == record_id, field
        ].iloc[0]

        with st.form("edit_record"):
            new_text = st.text_input(
                "New value", value="" if pd.isna(old_value) else str(old_value)
            )
            edit_clicked = st.form_submit_button("Save Changes")

        if edit_clicked:
            try:
                if not new_text.strip():
                    value = np.nan
                elif field in parameters or pd.api.types.is_numeric_dtype(data[field]):
                    value = float(new_text)
                    if not np.isfinite(value):
                        raise ValueError("Enter a valid number.")
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


with delete_tab:
    if data.empty:
        st.info("No records to delete.")
    else:
        record_id = st.selectbox(
            "Record ID to delete", data["Record_ID"].astype(str).tolist(),
            key="delete_id"
        )
        confirm = st.checkbox("Confirm deletion")

        if st.button("Delete Record"):
            if not confirm:
                st.warning("Please confirm before deleting.")
            else:
                try:
                    updated = data[
                        data["Record_ID"].astype(str) != record_id
                    ].copy()
                    save_data(updated)
                    st.success("Record deleted.")
                    st.rerun()
                except (ValueError, OSError) as error:
                    st.error(str(error))
