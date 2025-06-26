import pandas as pd
from sqlalchemy import create_engine
# ------------------------------------------------------------ #

# Step 1: Load the CSV file
csv_file_path = './csv/last_5_ys_yealy_stats.csv'
df = pd.read_csv(csv_file_path)

# Step 2: Create the database (SQLite in this example)
engine = create_engine('sqlite:///baseball_data.db')  # Creates file my_database.db

# Step 3: Write the dataframe to a table in the database
df.to_sql('your_table_name', con=engine, index=False, if_exists='replace')
