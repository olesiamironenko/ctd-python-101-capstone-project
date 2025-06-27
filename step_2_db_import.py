import os
import pandas as pd
from sqlalchemy import create_engine, text

# -----------------------------
# CONFIGURATION
# -----------------------------
CSV_DIR = 'csv'  # folder with CSVs
db_folder = 'db'
db_name = 'baseball_stats.db'
schema_file = os.path.join(db_folder, 'schema.sql')
db_path = os.path.join(db_folder, db_name)

# -----------------------------
# STEP 1: CREATE DB FOLDER
# -----------------------------
os.makedirs(db_folder, exist_ok=True)

# -----------------------------
# STEP 2: DEFINE AND WRITE SCHEMA
# -----------------------------
schema_sql = """
CREATE TABLE IF NOT EXISTS stat_titles (
    stat_title_id INTEGER PRIMARY KEY,
    stat_title TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS statistics (
    statistic_id INTEGER PRIMARY KEY,
    statistic TEXT NOT NULL,
    stat_title_id INTEGER NOT NULL,
    FOREIGN KEY (stat_title_id) REFERENCES stat_titles(stat_title_id)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS years (
    year_id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS leagues (
    league_id INTEGER PRIMARY KEY,
    league TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS last_5_ys_yearly_stats (
    statistic_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    no REAL,
    top_25 TEXT,
    year_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    FOREIGN KEY (statistic_id) REFERENCES statistics(statistic_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (year_id) REFERENCES years(year_id),
    FOREIGN KEY (league_id) REFERENCES leagues(league_id)
);
"""

with open(schema_file, 'w') as f:
    f.write(schema_sql)

# -----------------------------
# STEP 3: EXECUTE SCHEMA
# -----------------------------
engine = create_engine(f'sqlite:///{db_path}')

raw_conn = engine.raw_connection()
try:
    cursor = raw_conn.cursor()
    with open(schema_file, 'r') as f:
        cursor.executescript(f.read())
    raw_conn.commit()
finally:
    raw_conn.close()

# -----------------------------
# STEP 4: IMPORT CSV FILES TO DB
# -----------------------------
# Map CSV file names to table names (adjust as needed)
csv_to_table = {
    'stat_titles.csv': 'stat_titles',
    'statistics.csv': 'statistics',
    'teams.csv': 'teams',
    'players.csv': 'players',
    'years.csv': 'years',
    'leagues.csv': 'leagues',
    'last_5_ys_yearly_stats.csv': 'last_5_ys_yearly_stats'
}

for filename, table_name in csv_to_table.items():
    path = os.path.join(CSV_DIR, filename)
    if os.path.exists(path):
        print(f"Importing {filename} into table '{table_name}'...")
        df = pd.read_csv(path)
        df.to_sql(table_name, engine, if_exists='replace', index=False)
    else:
        print(f"WARNING: {filename} not found in {CSV_DIR}!")