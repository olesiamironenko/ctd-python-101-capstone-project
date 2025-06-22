import pandas as pd
import numpy as np
import warnings
from pandas.errors import ParserWarning

warnings.simplefilter(action='ignore', category=ParserWarning)
# ------------------------------------------------------------------
# Cleaning df
def clean_df(df):
    df = df.replace(["To Be Determined", "--"], np.nan).copy()
    df = df.dropna().drop_duplicates().reset_index(drop=True)
    return df

# ------------------------------------------------------------------



# al_nl_teams = pd.read_csv('./al_nl_teams.csv')
# al_pitching_statistics_league_leaders = pd.read_csv('./al_pitching_statistics_league_leaders.csv')
# fielding = pd.read_csv('./fielding.csv')
# hitting = pd.read_csv('./hitting.csv')
# nl_hitting_statistics_league_leaders = pd.read_csv('./nl_hitting_statistics_league_leaders.csv')
# nl_pitching_statistics_league_leaders = pd.read_csv('./nl_pitching_statistics_league_leaders.csv')
# pitching = pd.read_csv('./pitching.csv')
# roster = pd.read_csv('./roster.csv')
# schedule = pd.read_csv('./schedule.csv')


# al_nl_teams_clean = clean_df(al_nl_teams)
# al_pitching_statistics_league_leaders_clean = clean_df(al_pitching_statistics_league_leaders)
# fielding_clean = clean_df(fielding)
# hitting_clean = clean_df(hitting)
# nl_hitting_statistics_league_leaders_clean = clean_df(nl_hitting_statistics_league_leaders)
# nl_pitching_statistics_league_leaders_clean = clean_df(nl_pitching_statistics_league_leaders)
# pitching_clean = clean_df(pitching)
# roster_clean = clean_df(roster)
# schedule_clean = clean_df(schedule)

# print(al_nl_teams_clean.head())
# print(al_pitching_statistics_league_leaders_clean.head())
# print(fielding_clean.head())
# print(hitting_clean.head())
# print(nl_hitting_statistics_league_leaders_clean.head())
# print(nl_pitching_statistics_league_leaders_clean.head())
# print(pitching_clean.head())
# print(roster_clean.head())
# print(schedule_clean.head())


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

# Add player_id column
# Make sure the DataFrame index is 0…n-1 and unique
players = players.reset_index(drop=True)

# Create id
players["player_id"] = pd.Series(range(len(players)), dtype="int64") 

# print(players["player_id"].dtype)
# print(players.head())
# print(players.columns)

# Clean al_hitting_statistics_league_leaders
al_hitting_statistics_league_leaders = pd.read_csv('./al_hitting_statistics_league_leaders.csv')
al_hitting_statistics_league_leaders_clean = clean_df(al_hitting_statistics_league_leaders)
# print(al_hitting_statistics_league_leaders_clean.head())

# Create separate dfs for:
# Statistics
# Keep rows where 'Statistic' does NOT start with a digit
# Mask for rows where Statistic does NOT start with a digit
valid_stat_mask = ~al_hitting_statistics_league_leaders_clean["Statistic"].str.match(r"^\d", na=False)

# Extract unique valid statistics
unique_stats = (
    al_hitting_statistics_league_leaders_clean
    .loc[valid_stat_mask, "Statistic"]
    .dropna()
    .unique()
)

# Create statistics df
stats = pd.DataFrame({
    "statistic_id": range(len(unique_stats)),
    "statistic": unique_stats
})

# Keep rows with index ≤ 11 – slice by position if you prefer
stats = stats.iloc[:12].reset_index(drop=True)
# print(statistics)

# 
# Replace "Name" with player_id
# Make sure both columns exist and are typed correctly
# ------------------------------------------------------------------
players["player_id"] = players["player_id"].astype("int64")
players["Name"]      = players["Name"].astype(str).str.strip()

# Build the FK column from mapping
name_to_id = dict(zip(players["Name"], players["player_id"]))

print(al_hitting_statistics_league_leaders_clean.columns)

al_hitting_statistics_league_leaders_clean["player_id"] = al_hitting_statistics_league_leaders_clean["Name"].map(name_to_id)
#            ^ column now exists (may contain NaN for unmatched names)

al_hitting_statistics_league_leaders_clean["player_id"] = pd.to_numeric(
    al_hitting_statistics_league_leaders_clean["player_id"],
    errors="coerce"        # bad values become NaN
).astype("Int64")          # nullable integer that still allows <NA>
al_hitting_statistics_league_leaders_clean["Name"]        = al_hitting_statistics_league_leaders_clean["Name"].astype(str).str.strip()
# ------------------------------------------------------------------
# CHECK  — are the (player_id, Name) pairs identical?
# ------------------------------------------------------------------
check = (
    al_hitting_statistics_league_leaders_clean.merge(
        players[["player_id", "Name"]]
            .rename(columns={"Name": "Name_ref"}),
        on="player_id",
        how="left"
    )
)

mismatch = check[ check["Name"] != check["Name_ref"] ]

if mismatch.empty:
    print("✅ All player_id + Name pairs in stats agree with players.")
else:
    print("❌ Mismatching rows:")
    print(mismatch[["player_id", "Name", "Name_ref"]].head())
    #  Fix wrong names
    al_hitting_statistics_league_leaders_clean.loc[mismatch.index, "Name"] = mismatch["Name_ref"]

    # Fix wrong IDs (use name→id dict)
    name_to_id = dict(zip(players["Name"], players["player_id"]))
    al_hitting_statistics_league_leaders_clean["player_id"] = al_hitting_statistics_league_leaders_clean["Name"].map(name_to_id).astype("Int64")

    # Drop every stats row that failed to map to a player_id
    al_hitting_statistics_league_leaders_clean = (
        al_hitting_statistics_league_leaders_clean
            .dropna(subset=["player_id"])      # remove NaN / <NA> IDs
            .reset_index(drop=True)            # tidy up the index
    )

    # re-check
    if (al_hitting_statistics_league_leaders_clean.merge(players[["player_id","Name"]],
                    on=["player_id","Name"],
                    how="left").isna().any().any()):
        raise ValueError("Some player rows still don’t match — inspect manually.")
    else:
        print("✅ Stats table repaired: all pairs now match players.")

# Drop "Name" column
al_hitting_statistics_league_leaders_clean = al_hitting_statistics_league_leaders_clean.drop(columns=["Name"])


# 
# Replace "Team" with team_id
# Make sure both columns exist and are typed correctly
# ------------------------------------------------------------------
print(teams.columns)
teams["team_id"] = teams["team_id"].astype("int64")
teams["Name"]      = teams["Name"].astype(str).str.strip()

# Build the FK column from mapping
name_to_id = dict(zip(players["Name"], players["player_id"]))

print(al_hitting_statistics_league_leaders_clean.columns)

al_hitting_statistics_league_leaders_clean["player_id"] = al_hitting_statistics_league_leaders_clean["Name"].map(name_to_id)
#            ^ column now exists (may contain NaN for unmatched names)

al_hitting_statistics_league_leaders_clean["player_id"] = pd.to_numeric(
    al_hitting_statistics_league_leaders_clean["player_id"],
    errors="coerce"        # bad values become NaN
).astype("Int64")          # nullable integer that still allows <NA>
al_hitting_statistics_league_leaders_clean["Name"]        = al_hitting_statistics_league_leaders_clean["Name"].astype(str).str.strip()
# ------------------------------------------------------------------
# CHECK  — are the (player_id, Name) pairs identical?
# ------------------------------------------------------------------
check = (
    al_hitting_statistics_league_leaders_clean.merge(
        players[["player_id", "Name"]]
            .rename(columns={"Name": "Name_ref"}),
        on="player_id",
        how="left"
    )
)

mismatch = check[ check["Name"] != check["Name_ref"] ]

if mismatch.empty:
    print("✅ All player_id + Name pairs in stats agree with players.")
else:
    print("❌ Mismatching rows:")
    print(mismatch[["player_id", "Name", "Name_ref"]].head())
    #  Fix wrong names
    al_hitting_statistics_league_leaders_clean.loc[mismatch.index, "Name"] = mismatch["Name_ref"]

    # Fix wrong IDs (use name→id dict)
    name_to_id = dict(zip(players["Name"], players["player_id"]))
    al_hitting_statistics_league_leaders_clean["player_id"] = al_hitting_statistics_league_leaders_clean["Name"].map(name_to_id).astype("Int64")

    # Drop every stats row that failed to map to a player_id
    al_hitting_statistics_league_leaders_clean = (
        al_hitting_statistics_league_leaders_clean
            .dropna(subset=["player_id"])      # remove NaN / <NA> IDs
            .reset_index(drop=True)            # tidy up the index
    )

    # re-check
    if (al_hitting_statistics_league_leaders_clean.merge(players[["player_id","Name"]],
                    on=["player_id","Name"],
                    how="left").isna().any().any()):
        raise ValueError("Some player rows still don’t match — inspect manually.")
    else:
        print("✅ Stats table repaired: all pairs now match players.")

# Drop "Name" column
al_hitting_statistics_league_leaders_clean = al_hitting_statistics_league_leaders_clean.drop(columns=["Name"])


# Replace "Statistic" column with "statistic_id"
mask_not_digit = ~al_hitting_statistics_league_leaders_clean["Statistic"].str.match(r"^\d", na=False)
df_tmp = al_hitting_statistics_league_leaders_clean.loc[mask_not_digit]

# Now drop the rows where Statistic is NaN
al_hitting_statistics_league_leaders_clean = (
    df_tmp.dropna(subset=["Statistic"]).reset_index(drop=True)
)

# Keep only valid Statistic rows
#     • NOT starting with a digit
#     • NOT NaN
mask_valid = (
    ~al_hitting_statistics_league_leaders_clean["Statistic"].str.match(r"^\d", na=False)
) & (
    al_hitting_statistics_league_leaders_clean["Statistic"].notna()
)

al_hitting_statistics_league_leaders_clean = (
    al_hitting_statistics_league_leaders_clean
        .loc[mask_valid]
        .reset_index(drop=True)
)

# Map Statistic → statistic_id
stat_map = dict(zip(stats["statistic"], stats["statistic_id"]))

al_hitting_statistics_league_leaders_clean["statistic_id"] = (
    al_hitting_statistics_league_leaders_clean["Statistic"]
        .map(stat_map)
        .astype("int64")        # safe: no NaNs left after step 0
)

# Drop the text column
al_hitting_statistics_league_leaders_clean.drop(columns=["Statistic"], inplace=True)

# sanity-check
print(al_hitting_statistics_league_leaders_clean["statistic_id"].dtype)   # int64

print(al_hitting_statistics_league_leaders_clean.head())

print(al_hitting_statistics_league_leaders_clean.columns)

# -------------------------------------- #
# DFs to import to DB tables:
# 1. teams
# 2. hands
# 3. player_types
# 4. players
# 5. statistics

