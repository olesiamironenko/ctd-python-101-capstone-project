import pandas as pd
from sqlalchemy import create_engine
import os

# Step 1: Set paths
db_folder = 'db'
db_name = 'baseball_stats.db' 
csv_folder = 'csv'

# Step 2: Ensure the db folder exists
os.makedirs(db_folder, exist_ok=True)

# Step 3: Create SQLite engine inside db/ folder
db_path = os.path.join(db_folder, db_name)
engine = create_engine(f'sqlite:///{db_path}')

# Step 4: Define mapping: CSV filename -> table name
csv_table_map = {
    'stat_titles.csv': 'stat_titles',
    'statistics.csv': 'statistics',
    'teams.csv': 'teams',
    'players.csv': 'players',
    'years.csv': 'years',
    'leagues.csv': 'leagues',
    'last_5_ys_yealy_stats.csv': 'last_5_ys_yealy_stats',
}

# Step 5: Loop through CSVs and load into the database
for filename, table_name in csv_table_map.items():
    file_path = os.path.join(csv_folder, filename)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.to_sql(table_name, con=engine, index=False, if_exists='replace')
        print(f"Loaded '{filename}' into table '{table_name}'")
    else:
        print(f"! File not found: {file_path}")

# Confirm database was created
print(f"\n Database created at: {db_path}")