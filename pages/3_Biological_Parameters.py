
import streamlit as st
import pandas as pd
from classes.biological_data_manager import BiologicalDataManager

# Streamlit page configuration
st.set_page_config(
    page_title="Biological Parameters",
    page_icon="💧",
    layout="wide",
)
st.title("💧 Biological Water Quality")
st.caption("Andhra Pradesh | CPCB biological parameters dataset")

# Reading or loading the records from the CSV
manager = BiologicalDataManager()  # Object creation
try:
    df = manager.load_data()
except (FileNotFoundError, ValueError, OSError) as error:
    st.error(str(error))
    st.stop()  # prevents the further code to use df

measurement_columns = {
    "BOD (mg/L)": "Biochemical Oxygen Demand (mg/L)",
    "COD (mg/L)": "Chemical Oxygen Demand (mg/L)",
    "Fecal Coliform (MPN/100mL)": "Fecal Coliform (MPN/100mL)",
    "Total Coliform (MPN/100mL)": "Total Coliform (MPN/100mL)",
}

for column in measurement_columns.values():
    df[column] = pd.to_numeric(df[column], errors="coerce") # coerce makes the unkonown string as NaN

# Summary statistics
col1, col2, col3 = st.columns(3)
col1.metric("Total records", f"{len(df):,}")
col2.metric("Monitoring stations", f"{df['Station'].nunique():,}")
col3.metric("Districts", f"{df['District'].nunique():,}")


st.subheader("Measurement availability")
availability = pd.DataFrame({
    "Measurement": list(measurement_columns.keys()),
    "Available": [
        df[column].notna().sum() # notna() creates True for present values and false for others
        for column in measurement_columns.values()
    ], # List Comprehension
    "Missing": [
        df[column].isna().sum()
        for column in measurement_columns.values()
    ], # List Comprehension
})

# Displaying the read records
st.dataframe(availability, hide_index=True, use_container_width=True) # use_container_width-Make the table fill in the available horizontal space

st.subheader("Explore measurements")
measurement_label = st.selectbox("Choose a measurement",list(measurement_columns.keys()),)
# selectbox creates a dropdown menu


measurement_column = measurement_columns[measurement_label]
valid_values = df[measurement_column].dropna()

 # Handling the case when the values are empty and drawing charts appropriately
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

    chart_data = df[["District", measurement_column]].dropna() # Passing list of columns

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
    filtered = filtered[filtered["District"].isin(selected_districts)]# Boolean indexing

if search_station.strip(): 
    # It removes whitespaces in the start and end, not in the middle
    filtered = filtered[
        filtered["Station"].str.contains(
            search_station.strip(),
            case=False, # Ignores uppercase,lowercase differences
            na=False,   # Treat the missing stations as non matches
            regex=False,
        )
    ]

sort_column = st.selectbox(
    "Sort records by",
    ["Station", "District", "Data Acquisition Time"],
)

filtered = filtered.sort_values(
    sort_column,
    na_position="last",  # Place the missing values in the last
)

st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
st.dataframe(filtered, use_container_width=True, hide_index=True)

# CRUD OPERATIONS
st.divider() # Horizontal division(Seperation of records)
st.header("Manage Biological Records")

st.warning(
    "Changes are saved directly to the CSV file. "
    "Test with care and keep a backup."
)

add_tab, update_tab, delete_tab = st.tabs(
    ["Add Record", "Update Record", "Delete Record"]
)


def optional_number(value):
    """Return a number, or None when the input is blank."""
    value = value.strip()

    if not value:
        return None

    number = float(value)

    if not pd.notna(number) or number < 0:
        raise ValueError("Enter a valid non-negative number.")

    return number


measurement_columns_list = [
    "Biochemical Oxygen Demand (mg/L)",
    "Chemical Oxygen Demand (mg/L)",
    "Fecal Coliform (MPN/100mL)",
    "Total Coliform (MPN/100mL)",
]


# CREATE
# 1) Displaying the form
with add_tab:
    st.subheader("Add an observation")

    stations = sorted(df["Station"].dropna().unique().tolist())

    with st.form("add_record_form"):
        station = st.selectbox(
            "Monitoring station",
            stations,
        )

        acquisition_time = st.text_input(
            "Acquisition time (DD-MM-YYYY HH:MM)",
            placeholder="21-10-2026 08:30",
        )
# 2) Collecting input 
        bod = st.text_input("BOD (mg/L), optional")
        cod = st.text_input("COD (mg/L), optional")
        fecal = st.text_input("Fecal Coliform, optional")
        total = st.text_input("Total Coliform, optional")

        add_submitted = st.form_submit_button("Add observation")
# 3) Validating input
    if add_submitted:
        try:
            timestamp = acquisition_time.strip()
            if not timestamp:
                raise ValueError("Acquisition time is required.")
            parsed_time = pd.to_datetime(
                timestamp,
                format="%d-%m-%Y %H:%M",
                errors="coerce",
            )
            if pd.isna(parsed_time):
                raise ValueError(
                    "Use the format DD-MM-YYYY HH:MM."
                )

            values = {
                "Biochemical Oxygen Demand (mg/L)": optional_number(bod),
                "Chemical Oxygen Demand (mg/L)": optional_number(cod),
                "Fecal Coliform (MPN/100mL)": optional_number(fecal),
                "Total Coliform (MPN/100mL)": optional_number(total),
            }

            # Reuse the station's existing metadata.
            # 4) Building a record and save it
            station_rows = df[df["Station"] == station]
            record = station_rows.iloc[0].to_dict()

            numeric_ids = pd.to_numeric(df["SlNo"], errors="coerce")
            # Generating a new ID(Sl No) to add in the record
            if numeric_ids.isna().any():
                raise ValueError(
                    "Some existing record IDs are not numeric. "
                    "Correct the dataset before adding records."
                )

            record["SlNo"] = int(numeric_ids.max()) + 1
            record["Data Acquisition Time"] = timestamp
            record.update(values)
            manager.add_record(record)

            # Confirmation status of Create Operation
            st.success("Observation added successfully.")
            st.rerun()
        except (ValueError, OSError) as error:
            st.error(str(error))

# The record is actually getting saved in the BiologicalDataManager.addrecord() method

# UPDATE
with update_tab:
    st.subheader("Update a measurement")
    record_ids = df["SlNo"].dropna().tolist()
    if df.empty or not record_ids:
        st.info("No records are available to update.")
    else:
        # Takes the record ID, measurement to update, New value
        with st.form("update_record_form"):
            selected_id = st.selectbox(
                "Record ID",
                record_ids,
            )
            selected_measurement = st.selectbox(
                "Measurement",
                measurement_columns_list,
            )
            new_value_text = st.text_input(
                "New value (leave blank to mark it missing)"
            )
            update_submitted = st.form_submit_button("Save update")
        # Processing the update 
        if update_submitted:
            try:
                new_value = optional_number(new_value_text) # Validates the new measurement

                manager.update_record(
                    selected_id,
                    {selected_measurement: new_value},
                )
                # Confirmation status for the Update Operation
                st.success("Record updated successfully.")
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))

# DELETE
with delete_tab:
    st.subheader("Delete a record")
    record_ids = df["SlNo"].dropna().tolist()
    # User selects an ID
    if df.empty or not record_ids:
        st.info("No records are available to delete.")
    else:
        selected_delete_id = st.selectbox(
            "Record ID to delete",
            record_ids,
            key="delete_record_id",
        )

        st.write("Check the selected record before deleting it.")
        # Preview the selected record before deleting
        preview = df[
            df["SlNo"].astype(str) == str(selected_delete_id)
        ]

        st.dataframe(
            preview[
                [
                    "SlNo",
                    "Station",
                    "District",
                    "Data Acquisition Time",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )
        # Confirm the deletion
        confirm_delete = st.checkbox(
            f"Confirm deletion of record {selected_delete_id}"
        )

        if st.button("Delete selected record", type="primary"): # important button style as deletion is dangerous
            if not confirm_delete:
                st.warning("Please confirm before deleting.")
            else:
                try:
                    manager.delete_record(selected_delete_id)

                    st.success("Record deleted successfully.")
                    st.rerun()

                except (ValueError, OSError) as error:
                    st.error(str(error))
