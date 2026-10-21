
import streamlit as st
import pandas as pd

from classes.biological_data_manager import BiologicalDataManager


st.set_page_config(
    page_title="Biological Parameters",
    page_icon="💧",
    layout="wide",
)

st.title("💧 Biological Water Quality")
st.caption("Andhra Pradesh | CPCB biological parameters dataset")

manager = BiologicalDataManager()

try:
    df = manager.load_data()
except (FileNotFoundError, ValueError, OSError) as error:
    st.error(str(error))
    st.stop()

measurement_columns = {
    "BOD (mg/L)": "Biochemical Oxygen Demand (mg/L)",
    "COD (mg/L)": "Chemical Oxygen Demand (mg/L)",
    "Fecal Coliform (MPN/100mL)": "Fecal Coliform (MPN/100mL)",
    "Total Coliform (MPN/100mL)": "Total Coliform (MPN/100mL)",
}

for column in measurement_columns.values():
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Summary statistics
col1, col2, col3 = st.columns(3)

col1.metric("Total records", f"{len(df):,}")
col2.metric("Monitoring stations", f"{df['Station'].nunique():,}")
col3.metric("Districts", f"{df['District'].nunique():,}")

st.subheader("Measurement availability")

availability = pd.DataFrame({
    "Measurement": list(measurement_columns.keys()),
    "Available": [
        df[column].notna().sum()
        for column in measurement_columns.values()
    ],
    "Missing": [
        df[column].isna().sum()
        for column in measurement_columns.values()
    ],
})

st.dataframe(availability, hide_index=True, use_container_width=True)

st.subheader("Explore measurements")

measurement_label = st.selectbox(
    "Choose a measurement",
    list(measurement_columns.keys()),
)

measurement_column = measurement_columns[measurement_label]
valid_values = df[measurement_column].dropna()

if valid_values.empty:
    st.warning(
        f"No recorded values are available for {measurement_label}. "
        "The chart cannot be generated."
    )
else:
    stat1, stat2, stat3 = st.columns(3)
    stat1.metric("Mean", f"{valid_values.mean():,.2f}")
    stat2.metric("Median", f"{valid_values.median():,.2f}")
    stat3.metric("Maximum", f"{valid_values.max():,.2f}")

    chart_data = df[["District", measurement_column]].dropna()

    st.subheader(f"{measurement_label}: Distribution")
    st.bar_chart(
        chart_data.groupby("District")[measurement_column]
        .mean()
        .sort_values(ascending=False)
        .head(15)
    )

    st.subheader(f"{measurement_label}: Value distribution")
    st.histogram if False else None
    st.line_chart(
        valid_values.reset_index(drop=True),
        height=250,
    )

st.subheader("Search and filter records")

districts = sorted(df["District"].dropna().unique().tolist())
selected_districts = st.multiselect(
    "Filter by district",
    options=districts,
    default=[],
)

search_station = st.text_input("Search station name")

filtered = df.copy()

if selected_districts:
    filtered = filtered[filtered["District"].isin(selected_districts)]

if search_station.strip():
    filtered = filtered[
        filtered["Station"].str.contains(
            search_station.strip(),
            case=False,
            na=False,
            regex=False,
        )
    ]

sort_column = st.selectbox(
    "Sort records by",
    ["Station", "District", "Data Acquisition Time"],
)

filtered = filtered.sort_values(
    sort_column,
    na_position="last",
)

st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
st.dataframe(filtered, use_container_width=True, hide_index=True)
