
from pathlib import Path
import pandas as pd
import streamlit as st

from classes.physical_data_manager import PhysicalDataManager

st.set_page_config(
    page_title="Physical Water Quality",
    page_icon="💧",
    layout="wide"
)

ROOT = Path(__file__).resolve().parents[1]
manager = PhysicalDataManager(
    ROOT / "data" / "physical_parameters_app.csv"
)

PARAMETERS = {
    "Temperature (°C)": "temperature_c",
    "pH": "ph",
    "Turbidity (NTU)": "turbidity_ntu",
    "Conductivity (µS/cm)": "conductivity_us_cm",
    "Total Dissolved Solids (mg/L)": "tds_mg_l",
    "Dissolved Oxygen (mg/L)": "dissolved_oxygen_mg_l",
}

st.markdown("""
<style>
.block-container {padding-top: 2rem;}
[data-testid="stMetric"] {
    background: rgba(30, 150, 145, 0.10);
    border: 1px solid rgba(30, 150, 145, 0.3);
    padding: 15px;
    border-radius: 12px;
}
h1 {color: #239B91;}
</style>
""", unsafe_allow_html=True)


def load_data():
    data = manager.read_data()
    for column in PARAMETERS.values():
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


try:
    df = load_data()
except Exception as error:
    st.error(f"Could not load data: {error}")
    st.stop()


# DASHBOARD
st.title("💧 Physical Water Quality")
st.caption("Water monitoring, measurement analysis and record management")

c1, c2, c3 = st.columns(3)
c1.metric("Total Records", len(df))
c2.metric("Monitoring Locations", df["location"].nunique())
c3.metric(
    "Available Measurements",
    int(sum(df[col].notna().sum() for col in PARAMETERS.values()))
)

# STATISTICS AND DATA QUALITY
st.subheader("📊 Measurement Availability")

availability = []
for label, column in PARAMETERS.items():
    count = int(df[column].notna().sum())
    availability.append({
        "Parameter": label,
        "Available Readings": count,
        "Missing Readings": len(df) - count
    })

st.dataframe(
    pd.DataFrame(availability),
    use_container_width=True,
    hide_index=True
)

# VISUALIZATION
st.subheader("📈 Explore Measurements")

selected_parameter = st.selectbox(
    "Choose a parameter",
    list(PARAMETERS.keys()),
    index=3
)

column = PARAMETERS[selected_parameter]
valid = df.dropna(subset=[column]).copy()

if not valid.empty:
    values = valid[column]

    c1, c2, c3 = st.columns(3)
    c1.metric("Average", f"{values.mean():.2f}")
    c2.metric("Median", f"{values.median():.2f}")
    c3.metric("Maximum", f"{values.max():.2f}")

    location_values = (
        valid.groupby("location")[column]
        .mean()
        .sort_values(ascending=False)
        .head(15)
    )

    st.markdown(f"#### Average {selected_parameter} by Location")
    st.bar_chart(location_values)

    st.markdown(f"#### {selected_parameter} Distribution")
    distribution = pd.cut(values, bins=10, duplicates="drop")
    counts = distribution.value_counts().sort_index()
    counts.index = counts.index.astype(str)
    st.bar_chart(counts)
else:
    st.info(
        f"No actual {selected_parameter} readings are available. "
        "Select another parameter or add a record with measurements."
    )

# SEARCH, FILTER AND SORT
st.divider()
st.subheader("🔎 Search & Filter Records")

search = st.text_input(
    "Search by Record ID or Location",
    placeholder="Example: 9999 or TEST STATION"
)

locations = sorted(df["location"].dropna().astype(str).unique())

c1, c2 = st.columns(2)
with c1:
    selected_locations = st.multiselect(
        "Filter by location", locations
    )
with c2:
    sort_order = st.selectbox(
        "Sort records by ID",
        ["Highest ID first", "Lowest ID first"]
    )

filtered = df.copy()

if search.strip():
    query = search.strip()
    filtered = filtered[
        filtered["record_id"].astype(str).str.contains(
            query, case=False, na=False
        )
        | filtered["location"].astype(str).str.contains(
            query, case=False, na=False
        )
    ]

if selected_locations:
    filtered = filtered[
        filtered["location"].astype(str).isin(selected_locations)
    ]

filtered = filtered.sort_values(
    "record_id",
    ascending=(sort_order == "Lowest ID first"),
    na_position="last"
)

display_names = {
    "record_id": "Record ID",
    "sample_date": "Sample Date",
    "location": "Location",
    **{value: label for label, value in PARAMETERS.items()}
}

st.caption(f"Showing {len(filtered)} of {len(df)} records")
st.dataframe(
    filtered.rename(columns=display_names),
    use_container_width=True,
    hide_index=True
)

# CREATE
st.divider()
st.subheader("➕ Add Record")

with st.form("add_record"):
    record_id = st.number_input("Record ID", min_value=1, step=1)
    sample_date = st.date_input("Sample Date")
    location = st.text_input("Location")
    temperature = st.number_input("Temperature (°C)", min_value=0.0)
    ph = st.number_input("pH", min_value=0.0, max_value=14.0)
    turbidity = st.number_input("Turbidity (NTU)", min_value=0.0)
    conductivity = st.number_input("Conductivity (µS/cm)", min_value=0.0)

    add_clicked = st.form_submit_button("Add Record")

if add_clicked:
    if not location.strip():
        st.error("Please enter a location.")
    else:
        try:
            manager.create_record({
                "record_id": int(record_id),
                "sample_date": str(sample_date),
                "location": location.strip(),
                "temperature_c": temperature,
                "ph": ph,
                "turbidity_ntu": turbidity,
                "conductivity_us_cm": conductivity,
                "tds_mg_l": float("nan"),
                "dissolved_oxygen_mg_l": float("nan")
            })
            st.success("Record added successfully!")
            st.rerun()
        except Exception as error:
            st.error(str(error))

# UPDATE
st.subheader("✏️ Update Record")

with st.form("update_record"):
    update_id = st.number_input(
        "Record ID to update", min_value=1, step=1, key="update_id"
    )
    new_location = st.text_input("New Location")
    new_temperature = st.number_input(
        "New Temperature (°C)", min_value=0.0, key="new_temperature"
    )
    update_clicked = st.form_submit_button("Update Record")

if update_clicked:
    try:
        changes = {"temperature_c": new_temperature}
        if new_location.strip():
            changes["location"] = new_location.strip()

        manager.update_record(int(update_id), changes)
        st.success("Record updated successfully!")
        st.rerun()
    except Exception as error:
        st.error(str(error))

# DELETE
st.subheader("🗑️ Delete Record")

with st.form("delete_record"):
    delete_id = st.number_input(
        "Record ID to delete", min_value=1, step=1, key="delete_id"
    )
    delete_clicked = st.form_submit_button("Delete Record")

if delete_clicked:
    try:
        manager.delete_record(int(delete_id))
        st.success("Record deleted successfully!")
        st.rerun()
    except Exception as error:
        st.error(str(error))
