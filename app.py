
import streamlit as st

st.set_page_config(
    page_title="AquaMonitor | Water Quality System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Header ---
st.title("💧 Water Quality System")
st.caption("Explore water-quality data. Discover meaningful insights.")

st.divider()

# --- Hero section ---
st.subheader("Understand our water. Protect our future.")

st.write(
    "Explore water-quality observations, analyse biological, "
    "chemical and physical parameters, and discover insights "
    "from environmental data."
)

st.info(
    "Choose a parameter module below or use the navigation "
    "menu in the sidebar to explore the system."
)

# --- Parameter modules ---
st.subheader("Explore Water Quality Parameters")

st.write(
    "Select a module to explore its dataset, visualizations "
    "and available record-management features."
)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("🧬 Biological Parameters")
        st.write(
            "Explore BOD, COD, fecal coliform and total "
            "coliform observations."
        )
        st.caption(
            "Charts, statistics, search, filtering and CRUD."
        )
        st.page_link(
            "pages/3_Biological_Parameters.py",
            label="Explore Biological Data",
            icon="🧬",
            use_container_width=True,
        )

with col2:
    with st.container(border=True):
        st.subheader("🧪 Chemical Parameters")
        st.write(
            "Explore chemical measurements used to understand "
            "water composition and quality."
        )
        st.caption("More features will be available soon.")
        st.info("🧪 Coming Soon!")

with col3:
    with st.container(border=True):
        st.subheader("🌊 Physical Parameters")
        st.write(
            "Explore physical characteristics of water, "
            "depending on the measurements in the dataset."
        )
        st.caption("More features will be available soon.")
        st.info("🌊 Coming Soon!")

# --- Project overview ---
st.divider()
st.subheader("About the System")

about1, about2, about3 = st.columns(3, gap="medium")

with about1:
    with st.container(border=True):
        st.markdown("### 📊 Explore")
        st.write(
            "View available observations, summaries "
            "and visualizations."
        )

with about2:
    with st.container(border=True):
        st.markdown("### 🔎 Analyse")
        st.write(
            "Search, filter and sort records to find "
            "relevant information."
        )

with about3:
    with st.container(border=True):
        st.markdown("### 🗂️ Manage")
        st.write(
            "Create, read, update and delete observations "
            "where supported by each module."
        )

# --- Data note ---
st.divider()
st.subheader("About the Data")

st.write(
    "The system brings together water-quality datasets "
    "assigned to the different project modules."
)

st.warning(
    "Some measurements may be missing. Missing values are "
    "not treated as zero, and unavailable values should not "
    "be interpreted as measured results."
)

# --- Footer ---
st.divider()

st.caption(
    "AquaMonitor | Water Quality Monitoring System | Academic Project"
)
