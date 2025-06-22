import pandas as pd
import numpy as np

# ------------------------------------------------------------------
# Cleaning df
def clean_df(df):
    df = df.replace(["To Be Determined", "--"], np.nan).copy()
    df = df.dropna().drop_duplicates().reset_index(drop=True)
    return df

# ------------------------------------------------------------------

# Cleaning roster.csv
# Add column names 
col_names = ["Team", "No", "Name", "Height", "Weight", "Throws", "Bats", "DOB"]

# Define and skip bad rows:
def skip_if_short(fields):
    """Skip any line that has < 8 comma-separated fields."""
    return None if len(fields) < 8 else fields

# Open roster.csv, no headers, column names added, bad rows skipped
roster = pd.read_csv(
    "roster.csv",
    header=None,
    names=col_names,     # give the DF its 10 columns up front
    engine="python",     # callable only works with the Python parser
    on_bad_lines=skip_if_short,
    quoting=3            # ignore stray quotes if the file has none
)

# Add a column with player types based on values in column "Name"
# 1.  Capture the header text *only* on rows where the first column equals '#'
roster['Player Type'] = roster['Name'].where(roster['No'] == '#')

# 2.  Forward-fill so every subsequent row inherits the last seen header text
roster['Player Type'] = roster['Player Type'].ffill()

# 3.  Drop the header rows themselves
roster = roster[roster['No'] != '#'].reset_index(drop=True)

# # 4.  Inspect the result
# print(roster[['Name', 'Player Type']].head(20))   # first 20 rows
# print(roster['Player Type'].value_counts())       # how many rows per section

roster = clean_df(roster)

# print(roster.tail(5))  # Check the result
# print(roster)

# Create separate dfs for:
# Teams
teams = roster[["Team"]].drop_duplicates().reset_index(drop=True)
teams["team_id"] = teams.index + 1
# print(teams_df)

# Hands (for Trows and Bats)
# Collect every distinct value that appears in either column
hand_values = (
    pd.concat([roster["Throws"], roster["Bats"]])
      .dropna()
      .str.strip()
      .unique()
)

# Filter: keep only values containing at least one letter (A-Z, case-insensitive)
filtered_hands = [h for h in hand_values if pd.notna(h) and any(c.isalpha() for c in str(h))]

# Create hands lookup table
hands = pd.DataFrame({"hand": sorted(filtered_hands)}).reset_index().rename(columns={"index": "hand_id"})
# print(hands)

# Player Types
# Get unique Player Types, sorted
unique_types = sorted(roster["Player Type"].dropna().unique())

# Create player_types lookup table with IDs
player_types = pd.DataFrame({
    "player_type_id": range(len(unique_types)),
    "player_type": unique_types
})
# print(player_types)

# Players
# Convert Player Name to string explicitly
roster["Name"] = roster["Name"].astype(str).str.strip()

# Keep only rows where Name does NOT start with a digit
roster = roster[~roster["Name"].str.match(r'^\d')]

# Convert "No" to integer
roster["No"] = pd.to_numeric(roster["No"].astype(str).str.extract(r'(\d+)')[0], errors='coerce').astype('Int64')

# Convert DOB to datetime (errors='coerce' will set bad parses to NaT)
roster["DOB"] = pd.to_datetime(roster["DOB"], errors='coerce')

# Map Team, Throws, Bats, Player Type to their IDs:
team_map = dict(zip(teams["Team"], teams["team_id"]))
hand_map = dict(zip(hands["hand"], hands["hand_id"]))
player_type_map = dict(zip(player_types["player_type"], player_types["player_type_id"]))

roster["team_id"] = roster["Team"].map(team_map)
roster["throws_id"] = roster["Throws"].str.strip().map(hand_map)
roster["bats_id"] = roster["Bats"].str.strip().map(hand_map)
roster["player_type_id"] = roster["Player Type"].map(player_type_map)

# Drop the columns no longer needed:
players = roster.drop(columns=["Team", "Throws", "Bats", "Player Type", "Height", "Weight"])

# Reorder columns as needed
players = players[
    ["team_id", "No", "Name", "DOB", "player_type_id", "throws_id", "bats_id"]
]
print(players)