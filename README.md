# Baseball Statistics Dashboard (2021–2024)

This Streamlit web app provides an interactive dashboard to explore MLB player performance statistics from 2021 to 2024. It includes tools to view yearly leaders, compare leagues over time, and visualize standout players with interactive charts.

## Features

- Filter by year, league, and statistic group (Hitting or Pitching)
- View best players for specific statistics each year
- Compare leagues over time with line charts
- Sunburst chart of most consistent top performers by team
- Interactive UI with sidebar filters and charts powered by Plotly

## Tech Stack

- **Python 3.13**
- **Streamlit** – UI framework
- **Plotly** – Interactive charts
- **Pandas** – Data handling
- **SQLite** – Local database
- **SQLAlchemy** – ORM for DB access

## Directory Structure
.
├── step_4_dashboard.py # Main Streamlit app
├── db/
│ └── baseball_stats.db # SQLite database
├── requirements.txt
└── README.md

## Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/olesiamironenko/ctd-python-101-capstone-project.git
    cd ctd-python-101-capstone-project
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Launch the dashboard:

```bash
.venv/bin/streamlit run step_4_dashboard.py # On Windows: .venv\Scripts\streamlit run step_4_dashboard.py
```

## Notes
Make sure db/baseball_stats.db exists with the required schema and data.

The app assumes statistics and metadata (e.g. leagues, stat_titles) are available in related lookup tables.

## Screenshots
[Dashboard Overview: Yearly Best Results]
(screenshots/dahsboard_yearly_best_results_1.png)
(screenshots/dahsboard_yearly_best_results_2.png)
(screenshots/dahsboard_yearly_best_results_3.png)

[Dashboard Overview: Best Players]
(screenshots/dahsboard_best_players_1.png)
(screenshots/dahsboard_best_players_2.png)
(screenshots/dahsboard_best_players_3.png)

## License
MIT License – feel free to use and modify.