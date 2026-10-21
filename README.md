# Water-Quality-System
# 💧 Water Quality Monitoring System

A Python-based, interactive **Water Quality Monitoring System** built with Streamlit. The application provides a centralized interface for exploring water-quality datasets, visualizing measurements, searching and filtering records, and managing observations through Create, Read, Update, and Delete (CRUD) operations.

## 📌 Project Overview

Water quality monitoring helps organize and analyse observations collected from water-monitoring stations. This project demonstrates how Python, Pandas, and Streamlit can be used to build a data-driven application with an interactive dashboard and record-management functionality.

The application is organized into separate pages so that team members can develop modules for their assigned datasets or water-quality parameters.

## 🎯 Objectives

- Build an interactive web application using Python and Streamlit.
- Organize water-quality data in a structured format.
- Display summary statistics and visualizations.
- Search, filter, sort, and explore observations.
- Implement CRUD operations for managing records.
- Validate inputs and handle missing or invalid data.
- Apply object-oriented programming principles to data management.
- Collaborate through Git and GitHub using feature branches.

## ✨ Features

### 📊 Interactive Dashboard
- View dataset summaries and record counts.
- Explore measurement availability and descriptive statistics.
- Visualize available water-quality measurements.
- Search for stations and filter records by district.

### 🧪 Biological Parameters Module
The Biological Parameters page uses a CPCB biological-parameters dataset provided for the project.

It covers the following measurements:

- **Biochemical Oxygen Demand (BOD)** — mg/L
- **Chemical Oxygen Demand (COD)** — mg/L
- **Fecal Coliform** — MPN/100mL
- **Total Coliform** — MPN/100mL

The module also provides station and geographic information, acquisition dates, measurement summaries, and record-management tools.

**Data quality note:** Missing measurements are treated as missing values rather than zero. If a measurement column contains no recorded values, the application should communicate that limitation instead of presenting a misleading chart.

### 🗂️ CRUD Operations
The data-management layer provides:

- **Create:** Add a new observation.
- **Read:** Load and display existing records.
- **Update:** Modify a selected record using its ID.
- **Delete:** Remove a selected record after confirmation.

Validation includes record-ID checks, duplicate detection, and measurement validation. CSV updates use a temporary file and replacement approach to reduce the risk of leaving a partially written file.

### 🔎 Search and Filtering
- Search monitoring station names.
- Filter records by district.
- Sort records by supported fields.
- View the filtered dataset in a table.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and data processing |
| Streamlit | Interactive web interface |
| Pandas | CSV handling, filtering, and analysis |
| NumPy | Numerical operations where needed |
| Matplotlib | Data visualization where used |
| Git and GitHub | Version control and team collaboration |
| CSV | Dataset storage |

## 📁 Project Structure

```text
Water-Quality-System/
├── app.py
├── pages/
│   └── 3_Biological_Parameters.py
├── classes/
│   ├── __init__.py
│   └── biological_data_manager.py
├── utils/
│   └── __init__.py
├── data/
│   └── biological_parameters.csv
├── requirements.txt
├── .gitignore
└── README.md
```

Additional pages and files may be added as other team modules are integrated.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or later
- pip
- Git

### 1. Clone the repository

```bash
git clone https://github.com/srichyavang-spec/Water-Quality-System.git
cd Water-Quality-System
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The application should open in your browser. Use the sidebar to navigate between the available pages.

## 🧑‍💻 Development Workflow

The project uses Git and GitHub for collaboration.

1. Create or switch to your assigned feature branch.
2. Implement and test your changes locally.
3. Review changes using `git status` and `git diff`.
4. Commit only the intended files.
5. Push your feature branch to GitHub.
6. Open a pull request for review before merging into `main`.

Example:

```bash
git checkout -b feature/your-module
git add .
git commit -m "Add your module"
git push -u origin feature/your-module
```

Review staged files before committing, and do not commit virtual environments, secrets, or temporary backup files.

## 📂 Data Source

The Biological Parameters module uses the CPCB biological-parameters dataset provided through the National Water Data Portal:

https://nwdp.nwic.gov.in/dataset/surface-water-quality-manual-biological-parameters-cpcb

Please refer to the source for dataset context and provenance. Check its applicable terms before redistributing the data.

## ⚠️ Data Limitations

- Some measurement fields may contain missing values.
- Missing values must not be interpreted as zero.
- A measurement with no available observations cannot support a meaningful statistical summary or chart.
- The application is an academic data-management and exploration project; it does not independently certify water safety or regulatory compliance.

## 👥 Team and Module Ownership

This is a collaborative academic project. Each team member is responsible for their assigned module and dataset.

| Team member | Module | Responsibility |
|---|---|---|
| Gorti Sri Chyavan | Biological Parameters | Dataset exploration, visualizations, and CRUD operations |
| Other team members | Assigned modules | To be completed with the actual names and module assignments |

## 🔮 Future Improvements

- Integrate all team members' modules into a unified dashboard.
- Improve chronological date handling and time-based visualizations.
- Add filtered report exports with timestamps.
- Expand automated validation and error-handling tests.
- Add automated tests for CRUD operations.
- Improve accessibility, responsive styling, and documentation.

## 📄 License

Add the license applicable to this project before distributing it publicly. Do not claim a license unless one has actually been selected and included in the repository.

---

**Built with Python, Streamlit, and Pandas as an academic team project.**
