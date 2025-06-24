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

    # Now drop the rows where Statistic is NaN
    df1 = (
        df_tmp.dropna(subset=[df1_col1]).reset_index(drop=True)
    )

    # Keep only valid Statistic rows
    #     • NOT starting with a digit
    #     • NOT NaN
    mask_valid = (
        ~df1[df1_col1].str.match(r"^\d", na=False)
    ) & (
        df1[df1_col1].notna()
    )

    df1_col1 = (
        df1_col1
            .loc[mask_valid]
            .reset_index(drop=True)
    )

    # Map Statistic → statistic_id
    df_map = dict(zip(df2[df2_col1], df2[df2_col2]))

    df1[df1_new_col] = (
        df1[df1_col1]
            .map(df_map)
            .astype("int64")        # safe: no NaNs left after step 0
    )

    # Drop the text column
    df1.drop(columns=[df1_col1], inplace=True)
    return df1
# ------------------------------------------------------------------