import pandas as pd
import numpy as np
import warnings
from pandas.errors import ParserWarning

warnings.simplefilter(action='ignore', category=ParserWarning)
# ------------------------------------------------------------------
# Standardize column names
def std_col_names(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(".", "_").str.replace(" ", "_").str.replace("#", "no")
    return df

# Replace nonsence values with NaN
def replace_nonsence(df):
    df = df.replace(["To Be Determined", "--"], np.nan).copy()
    return df

# Drop nas
def dropnas(df):
    df = df.dropna().drop_duplicates().reset_index(drop=True)
    return df

# Convert a column to integer:
def column_to_int(df, column_name):
    df[column_name] = df[column_name].astype(int)
    return df

# Keep only digits
def digits_only(df, column_name):
    df[column_name] = df[column_name].astype(str).str.replace(r"\D", "", regex=True)
    return df

# Drop rows where a column has no digits
def drop_non_digits(df, column_name):
    mask_has_digits = df[column_name].astype(str).str.contains(r"\d")
    df = df[mask_has_digits].reset_index(drop=True)
    return df

# Drop rows where one coli=unnm have specified value/values
def drop_rows_w_value(df, column, value):
    df = df[df[column] != value].reset_index(drop=True)
    return df

# Create separate dfs for future lookup table based on statistic column
def create_lookup_df(df, column_name, new_column_name_1, new_column_name_2):
    # Extract unique values
    unique_vals = (
        df[column_name]
        .dropna()
        .unique()
    )
    # Create lookup df
    new_df = pd.DataFrame({
        new_column_name_1: range(len(unique_vals)),
        new_column_name_2: unique_vals
    })
    return new_df

# Keep only rows where col starts with a letter
def col_val_start_letter(df, columnn_name):
    mask_starts_letter = df[columnn_name].astype(str).str.match(r"[A-Za-z]")
    df = df[mask_starts_letter].reset_index(drop=True)
    return df

# Replace text column with fk
def replace_txt_cloumn_with_fk(df1, df1_col1, df1_new_col, df2, df2_col1, df2_col2):
    mask_not_digit = ~df1[df1_col1].str.match(r"^\d", na=False)
    df_tmp = df1.loc[mask_not_digit]

    # Now drop the rows where the value is NaN
    df1 = (
        df_tmp.dropna(subset=[df1_col1]).reset_index(drop=True)
    )

    # Keep only valid df1 col1 rows
    #     • NOT starting with a digit
    #     • NOT NaN
    mask_valid = (
        ~df1[df1_col1].str.match(r"^\d", na=False)
    ) & (
        df1[df1_col1].notna()
    )

    df1 = (
        df1
            .loc[mask_valid]
            .reset_index(drop=True)
    )

    # Map df1 col1 -> df1 new col
    df_map = dict(zip(df2[df2_col1], df2[df2_col2]))

    df1[df1_new_col] = (
        df1[df1_col1]
            .map(df_map)
            .dropna()
            .astype("int64")
    )

    # Drop the text column
    df1.drop(columns=[df1_col1], inplace=True)
    return df1
# ------------------------------------------------------------------



# al_nl_teams = pd.read_csv('./al_nl_teams.csv')
# 
# 
# hitting = pd.read_csv('./hitting.csv')
# nl_hitting_statistics_league_leaders = pd.read_csv('./nl_hitting_statistics_league_leaders.csv')
# nl_pitching_statistics_league_leaders = pd.read_csv('./nl_pitching_statistics_league_leaders.csv')
# pitching = pd.read_csv('./pitching.csv')
# 
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

# ------------------------------------------ #
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

roster = std_col_names(roster)
print(roster.columns)

# Add a column with player types based on values in column "Name"
# 1.  Capture the header text *only* on rows where the first column equals '#'
roster['player_type'] = roster['name'].where(roster['no'] == '#')

# 2.  Forward-fill so every subsequent row inherits the last seen header text
roster['player_type'] = roster['player_type'].ffill()

# 3.  Drop the header rows themselves
roster = roster[roster['no'] != '#'].reset_index(drop=True)

# # 4.  Inspect the result
# print(roster[['Name', 'Player Type']].head(20))   # first 20 rows
# print(roster['Player Type'].value_counts())       # how many rows per section

roster = dropnas(roster)

# print(roster.tail(5))  # Check the result
# print(roster)

# ------------------------------------------- #
# Create separate dfs for:
# ------------------------------------------- #
# Teams
# ------------------------------------------- #
teams = roster[["team"]].drop_duplicates().reset_index(drop=True)
teams["team_id"] = teams.index + 1
# print(teams_df)
# ------------------------------------------- #

# ------------------------------------------- #
# Hands (for Trows and Bats)
# ------------------------------------------- #
# Collect every distinct value that appears in either column
hand_values = (
    pd.concat([roster["throws"], roster["bats"]])
      .dropna()
      .str.strip()
      .unique()
)

# Filter: keep only values containing at least one letter (A-Z, case-insensitive)
filtered_hands = [h for h in hand_values if pd.notna(h) and any(c.isalpha() for c in str(h))]

# Create hands lookup table
hands = pd.DataFrame({"hand": sorted(filtered_hands)}).reset_index().rename(columns={"index": "hand_id"})
# print(hands)

# ------------------------------------------- #
# Player Types
# ------------------------------------------- #
# Get unique Player Types, sorted
unique_types = sorted(roster["player_type"].dropna().unique())

# Create player_types lookup table with IDs
player_types = pd.DataFrame({
    "player_type_id": range(len(unique_types)),
    "player_type": unique_types
})
# print(player_types)

# ------------------------------------------- #
# Players
# ------------------------------------------- #
# Convert Player Name to string explicitly
roster["name"] = roster["name"].astype(str).str.strip()

# Keep only rows where Name does NOT start with a digit
roster = roster[~roster["name"].str.match(r'^\d')]

# Convert "No" to integer
roster["no"] = pd.to_numeric(roster["no"].astype(str).str.extract(r'(\d+)')[0], errors='coerce').astype('Int64')

# Convert DOB to datetime (errors='coerce' will set bad parses to NaT)
roster["dob"] = pd.to_datetime(roster["dob"], errors='coerce')

# Map Team, Throws, Bats, Player Type to their IDs:
team_map = dict(zip(teams["team"], teams["team_id"]))
hand_map = dict(zip(hands["hand"], hands["hand_id"]))
player_type_map = dict(zip(player_types["player_type"], player_types["player_type_id"]))

roster["team_id"] = roster["team"].map(team_map)
roster["throws_id"] = roster["throws"].str.strip().map(hand_map)
roster["bats_id"] = roster["bats"].str.strip().map(hand_map)
roster["player_type_id"] = roster["player_type"].map(player_type_map)

# Drop the columns no longer needed:
players = roster.drop(columns=["team", "throws", "bats", "player_type", "height", "weight"])

# Add player_id column
# Make sure the DataFrame index is 0…n-1 and unique
players = players.reset_index(drop=True)

# Create id
players["player_id"] = pd.Series(range(len(players)), dtype="int64") 

print(players.head())
players.info()

# ------------------------------------------ #

#------------------------------------------#
# Clean al_hitting_statistics_league_leaders
#------------------------------------------#
al_hitting_statistics_league_leaders = pd.read_csv('./al_hitting_statistics_league_leaders.csv')

al_hitting_statistics_league_leaders = std_col_names(al_hitting_statistics_league_leaders)

al_hitting_statistics_league_leaders = replace_nonsence(al_hitting_statistics_league_leaders)

al_hitting_statistics_league_leaders = dropnas(al_hitting_statistics_league_leaders)

print(f"\n al_hitting_statistics_league_leaders sample")
print(al_hitting_statistics_league_leaders.head())
al_hitting_statistics_league_leaders.info()

#------------------------------------------#
# Create separate dfs for:
#------------------------------------------#
# Statistics
#------------------------------------------#
# Keep rows where 'Statistic' does NOT start with a digit
# Mask for rows where Statistic does NOT start with a digit
valid_stat_mask = ~al_hitting_statistics_league_leaders["statistic"].str.match(r"^\d", na=False)

# Extract unique valid statistics
unique_stats = (
    al_hitting_statistics_league_leaders
    .loc[valid_stat_mask, "statistic"]
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

#------------------------------------------#
# Replace "name" with player_id
#------------------------------------------#
# Make sure both columns exist and are typed correctly
players["player_id"] = players["player_id"].astype("int64")
players["name"]      = players["name"].astype(str).str.strip()

# Build the FK column from mapping
name_to_id = dict(zip(players["name"], players["player_id"]))

al_hitting_statistics_league_leaders["player_id"] = al_hitting_statistics_league_leaders["name"].map(name_to_id)
# column now exists (may contain NaN for unmatched names)

al_hitting_statistics_league_leaders["player_id"] = pd.to_numeric(
    al_hitting_statistics_league_leaders["player_id"],
    errors="coerce"        # bad values become NaN
).astype("Int64")          # nullable integer that still allows <NA>
al_hitting_statistics_league_leaders["name"]        = al_hitting_statistics_league_leaders["name"].astype(str).str.strip()

# Drop every hitting stats row that failed to map to a player_id
al_hitting_statistics_league_leaders = (
    al_hitting_statistics_league_leaders
        .dropna(subset=["player_id"])      # remove NaN / <NA> IDs
        .reset_index(drop=True)            # tidy up the index
)

# CHeck if the (player_id, Name) pairs identical?
check = (
    al_hitting_statistics_league_leaders.merge(
        players[["player_id", "name"]]
            .rename(columns={"name": "name_ref"}),
        on="player_id",
        how="left"
    )
)

mismatch = check[ check["name"] != check["name_ref"] ]

if mismatch.empty:
    print("All player_id + Name pairs in stats agree with players.")
else:
    print("Mismatching rows:")
    print(mismatch[["player_id", "name", "name_ref"]].head())
    #  Fix wrong names
    al_hitting_statistics_league_leaders.loc[mismatch.index, "name"] = mismatch["name_ref"]

    # Fix wrong IDs (use name→id dict)
    name_to_id = dict(zip(players["name"], players["player_id"]))
    al_hitting_statistics_league_leaders["player_id"] = al_hitting_statistics_league_leaders["name"].map(name_to_id).astype("Int64")

    # re-check
    if (al_hitting_statistics_league_leaders.merge(players[["player_id","name"]],
                    on=["player_id","name"],
                    how="left").isna().any().any()):
        raise ValueError("Some player rows still don’t match — inspect manually.")
    else:
        print("Stats table repaired: all pairs now match players.")

# Drop "Name" column
al_hitting_statistics_league_leaders = al_hitting_statistics_league_leaders.drop(columns=["name"])


#------------------------------------------#
# Replace "Team" with team_id
#------------------------------------------#
# Make sure both columns exist and are typed correctly
print(teams.columns)
teams["team_id"] = teams["team_id"].astype("int64")
teams["team"]      = teams["team"].astype(str).str.strip()

# Build the FK column from mapping
team_to_id = dict(zip(teams["team"], teams["team_id"]))

al_hitting_statistics_league_leaders["team_id"] = al_hitting_statistics_league_leaders["team"].map(team_to_id)
# column now exists (may contain NaN for unmatched names)

al_hitting_statistics_league_leaders["team_id"] = pd.to_numeric(
    al_hitting_statistics_league_leaders["team_id"],
    errors="coerce"        # bad values become NaN
).astype("Int64")          # nullable integer that still allows <NA>
al_hitting_statistics_league_leaders["team"]        = al_hitting_statistics_league_leaders["team"].astype(str).str.strip()

# Drop every hitting stats row that failed to map to a team_id
al_hitting_statistics_league_leaders = (
    al_hitting_statistics_league_leaders
        .dropna(subset=["team_id"])      # remove NaN / <NA> IDs
        .reset_index(drop=True)            # tidy up the index
)

# Check if the (team_id, Team) pairs identical?
check = (
    al_hitting_statistics_league_leaders.merge(
        teams[["team_id", "team"]]
            .rename(columns={"team": "team_ref"}),
        on="team_id",
        how="left"
    )
)

mismatch = check[ check["team"] != check["team_ref"] ]

if mismatch.empty:
    print("All team_id + team pairs in stats agree with teams.")
else:
    print("Mismatching rows:")
    print(mismatch[["team_id", "team", "team_ref"]].head())
    #  Fix wrong teams
    al_hitting_statistics_league_leaders.loc[mismatch.index, "team"] = mismatch["team_ref"]

    # Fix wrong team IDs (use team→id dict)
    name_to_id = dict(zip(teams["team"], teams["team_id"]))
    al_hitting_statistics_league_leaders["team_id"] = al_hitting_statistics_league_leaders["team"].map(name_to_id).astype("Int64")

    # re-check
    if (al_hitting_statistics_league_leaders.merge(teams[["team_id","team"]],
                    on=["team_id"],
                    how="left").isna().any().any()):
        raise ValueError("Some player rows still don't match — inspect manually.")
    else:
        print("Stats table repaired: all pairs now match players.")

# Drop "Team" column
al_hitting_statistics_league_leaders = al_hitting_statistics_league_leaders.drop(columns=["team"])

al_hitting_statistics_league_leaders = al_hitting_statistics_league_leaders.dropna().reset_index(drop=True)

print(al_hitting_statistics_league_leaders.head())

#------------------------------------------#
# Replace "Statistic" column with "statistic_id"
#------------------------------------------#
mask_not_digit = ~al_hitting_statistics_league_leaders["statistic"].str.match(r"^\d", na=False)
df_tmp = al_hitting_statistics_league_leaders.loc[mask_not_digit]

# Now drop the rows where Statistic is NaN
al_hitting_statistics_league_leaders = (
    df_tmp.dropna(subset=["statistic"]).reset_index(drop=True)
)

# Keep only valid Statistic rows
#     • NOT starting with a digit
#     • NOT NaN
mask_valid = (
    ~al_hitting_statistics_league_leaders["statistic"].str.match(r"^\d", na=False)
) & (
    al_hitting_statistics_league_leaders["statistic"].notna()
)

al_hitting_statistics_league_leaders = (
    al_hitting_statistics_league_leaders
        .loc[mask_valid]
        .reset_index(drop=True)
)

# Map Statistic → statistic_id
stat_map = dict(zip(stats["statistic"], stats["statistic_id"]))

al_hitting_statistics_league_leaders["statistic_id"] = (
    al_hitting_statistics_league_leaders["statistic"]
        .map(stat_map)
        .astype("int64")        # safe: no NaNs left after step 0
)

# Drop the text column
al_hitting_statistics_league_leaders.drop(columns=["statistic"], inplace=True)

# sanity-check
print(f"\n al_hitting_statistics_league_leaders sample")
print(al_hitting_statistics_league_leaders.head())
al_hitting_statistics_league_leaders.info()
# -------------------------------------- #

# Clean year column
# Convert year column to integer
column_to_int(al_hitting_statistics_league_leaders, 'year')

# Clean # column
# Remove all non-digit characters
digits_only(al_hitting_statistics_league_leaders, 'no')
# -------------------------------------- #

# -------------------------------------- #
# Convert no column to integer
# -------------------------------------- #
al_hitting_statistics_league_leaders = column_to_int(al_hitting_statistics_league_leaders, 'no')
# -------------------------------------- #

# -------------------------------------- #
# Clean al_pitching_statistics_league_leaders
# -------------------------------------- #
# Load csv
al_pitching_statistics_league_leaders = pd.read_csv('./al_pitching_statistics_league_leaders.csv')

# Standardize column names
al_pitching_statistics_league_leaders = std_col_names(al_pitching_statistics_league_leaders)

# Replace nonsence values with NaN
al_pitching_statistics_league_leaders = replace_nonsence(al_pitching_statistics_league_leaders)

# Drop nas
al_pitching_statistics_league_leaders = dropnas(al_pitching_statistics_league_leaders)

# -------------------------------------- #
# Clean year column
# -------------------------------------- #
# Drop rows where year has no digits
al_pitching_statistics_league_leaders = drop_non_digits(al_pitching_statistics_league_leaders, 'year')

# Convert year to integer
al_pitching_statistics_league_leaders = column_to_int(al_pitching_statistics_league_leaders, 'year')
# -------------------------------------- #

# -------------------------------------- #
# Clean no column
# -------------------------------------- #
# Drop rows where no has no digits
al_pitching_statistics_league_leaders = drop_non_digits(al_pitching_statistics_league_leaders, 'no')
# -------------------------------------- #

# -------------------------------------- #
# Clean statistic column
# -------------------------------------- #
# 1. Create lookup df based on statistic column
# -------------------------------------- #
pitching_stats = create_lookup_df(al_pitching_statistics_league_leaders, 'statistic', 'p_statistic_id', 'p_statistic')

# Clean pitching_stats df: 
# keep only non-digits values
pitching_stats = col_val_start_letter(pitching_stats, 'p_statistic')

# Slice only statisstic related values
pitching_stats = pitching_stats.iloc[:5].reset_index(drop=True)
# -------------------------------------- #

# print("\n Quick check: pitching_stats")
# print(pitching_stats.head())
# pitching_stats.info()
# print("# -------------------------------------- #")

# -------------------------------------- #
# Switch statistic column in al_pitching_statistics_league_leaders to p_statistic_id from pitching_stats
# -------------------------------------- #
al_pitching_statistics_league_leaders = replace_txt_cloumn_with_fk(al_pitching_statistics_league_leaders, 'statistic', 'p_statistic_id', pitching_stats, 'p_statistic', 'p_statistic_id')

# -------------------------------------- #
# Final cleanup
# -------------------------------------- #
# Drop nas
al_pitching_statistics_league_leaders = dropnas(al_pitching_statistics_league_leaders)

# Convert plaier_id to integer
al_pitching_statistics_league_leaders['p_statistic_id'] = al_pitching_statistics_league_leaders['p_statistic_id'].astype(int)

# -------------------------------------- #
# Clean name column
# -------------------------------------- #
# 1. Clean name column from bad values
# -------------------------------------- #
al_pitching_statistics_league_leaders = col_val_start_letter(al_pitching_statistics_league_leaders, 'name')

# -------------------------------------- #
# 2. Switch name columnn to player_id from players
# -------------------------------------- #
print(players.columns)
al_pitching_statistics_league_leaders = replace_txt_cloumn_with_fk(al_pitching_statistics_league_leaders, 'name', 'player_id', players, 'name', 'player_id')

# -------------------------------------- #
# 3. Final cleanup
# -------------------------------------- #
# Drop nas
al_pitching_statistics_league_leaders = dropnas(al_pitching_statistics_league_leaders)

# Convert plaier_id to integer
al_pitching_statistics_league_leaders['player_id'] = al_pitching_statistics_league_leaders['player_id'].astype(int)

# -------------------------------------- #
# Clean team column
# -------------------------------------- #
# 1. Clean name column from bad values
# -------------------------------------- #
al_pitching_statistics_league_leaders = col_val_start_letter(al_pitching_statistics_league_leaders, 'team')

# -------------------------------------- #
# 2. Switch name columnn to player_id from players
# -------------------------------------- #
print(teams.columns)
al_pitching_statistics_league_leaders = replace_txt_cloumn_with_fk(al_pitching_statistics_league_leaders, 'team', 'team_id', teams, 'team', 'team_id')
# -------------------------------------- #

# -------------------------------------- #
# 3. Final cleanup
# -------------------------------------- #
# Drop nas
al_pitching_statistics_league_leaders = dropnas(al_pitching_statistics_league_leaders)

# Convert plaier_id to integer
al_pitching_statistics_league_leaders['team_id'] = al_pitching_statistics_league_leaders['team_id'].astype(int)
# -------------------------------------- #

# print("\n Quick check: al_pitching_statistics_league_leaders")
# print(al_pitching_statistics_league_leaders.head())
# al_pitching_statistics_league_leaders.info()
# print("# -------------------------------------- #")

# -------------------------------------- #
# Clean fielding df
# -------------------------------------- #
# Load df
# -------------------------------------- #
# Add column names
# -------------------------------------- #

# Open roster.csv, no headers, column names added, bad rows skipped
fielding = pd.read_csv(
    "fielding.csv",
    header=None
)

fielding.columns = ["name", "pos", "g", "gs", "outs", "tc", "ch", "po", "a", "e", "dp", "pb", "casb", "cacs", "fld_percentage"]


# -------------------------------------- #
# Clean team column
# -------------------------------------- #
# print(fielding['team'].value_counts())

# -------------------------------------- #
# Clean name column
# -------------------------------------- #
# print(fielding['name'].value_counts())


# fielding["name"] = fielding["name"].str.extract(r"([A-Z][a-z]+ [A-Z][a-z]+)$")

# -------------------------------------- #
# -------------------------------------- #

print("\n Quick check: fielding")
print(fielding.head())
fielding.info()
print("# -------------------------------------- #")


# print("\n Quick check: players")
# print(players.head())
# players.info()
# print("# -------------------------------------- #")


# -------------------------------------- #
# # DFs to import to DB tables:
# print("\n 1. teams"); teams.info()
# print("\n 2. hands"); hands.info()
# print("\n 3. player_types"); player_types.info()
# print("\n 4. players"); players.info()
# print("\n 5. statistics"); stats.info()
# print("\n 6. al_hitting_statistics_league_leaders"); al_hitting_statistics_league_leaders.info()
# print("\n 7. pitching statistics"); pitching_stats.info()
# print("\n 8. al_pitching_statistics_league_leaders"); al_pitching_statistics_league_leaders.info()

