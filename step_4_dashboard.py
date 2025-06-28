import streamlit as st  
import pandas as pd    
import os
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- Database connection setup ---
db_folder = 'db'
db_name = 'baseball_stats.db'
db_path = os.path.join(db_folder, db_name)
os.makedirs(db_folder, exist_ok=True)
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL)

# --- Helper Functions ---
def fetch_distinct_column_values(engine, table, column, order_by=None, fallback=None):
    try:
        order_clause = f"ORDER BY {order_by or column}"
        query = f"SELECT DISTINCT {column} FROM {table} {order_clause}"
        df = pd.read_sql(query, engine)
        values = df[column].astype(str).tolist()
        if not values:
            raise ValueError("No values found.")
        return values
    except Exception as e:
        if fallback:
            st.warning(f"Using fallback for {column} due to error: {e}")
            return fallback
        else:
            st.error(f"Failed to load {column} from {table}: {e}")
            return []

def fetch_statistics_by_title(engine, stat_title, fallback=None):
    try:
        query = text("""
            SELECT s.statistic 
            FROM statistics AS s
            JOIN stat_titles AS st ON s.stat_title_id = st.stat_title_id
            WHERE st.stat_title = :stat_title
            ORDER BY s.statistic
        """)
        df = pd.read_sql(query, engine, params={'stat_title': stat_title})
        values = df['statistic'].astype(str).tolist()
        if not values:
            raise ValueError("No statistics found.")
        return values
    except Exception as e:
        if fallback:
            st.warning(f"Using fallback statistics due to error: {e}")
            return fallback
        else:
            st.error(f"Failed to fetch statistics for {stat_title}: {e}")
            return []
        
# --- Dashboard functions ---

def get_statistics_by_league_stat_title(engine):
    st.title("Yearly Best Results (2021-2024)")

    # Fetch dropdown options with fallback
    leagues = fetch_distinct_column_values(engine, 
        'leagues', 'league', 
        fallback=['American League', 'National League'])
    
    stat_titles = fetch_distinct_column_values(engine, 
        'stat_titles', 'stat_title', 
        fallback=['Hitting Statistics', 'Pitching Statistics'])
    
    years = fetch_distinct_column_values(engine, 
        'years', 'year', 
        order_by='year', 
        fallback=[2021, 2022, 2023, 2024])
    years = sorted([int(y) for y in years])  # ensure int sorted

    # Sidebar selectors
    with st.sidebar:
        st.header("Filter Options")
        selected_league = st.radio("Select League", leagues)   
        selected_stat_title = st.radio("Select Statistic Group", stat_titles)
        selected_year = st.selectbox("Select Year", years, index=len(years)-2)


        # Define fallback options
        fallback_stats = {
            "Hitting Statistics": [
                "Base on Balls", "Batting Average", "Doubles", "Hits", "Home Runs", "On Base Percentage",
                "RBI", "Runs", "Slugging Average", "Stolen Bases", "Total Bases", "Triples"
            ],
            "Pitching Statistics": [
                "Complete Games", "ERA", "Games", "Saves", "Shutouts", "Strikeouts", "Winning Percentage", "Wins"
            ]
        }

        # Fetch list of statistics based on selected group
        statistic_options = fetch_statistics_by_title(engine, selected_stat_title, fallback=fallback_stats.get(selected_stat_title))
        selected_statistic = st.selectbox("Choose Specific Statistic", statistic_options)

    try:
        query = text("""
            SELECT 
                s.statistic AS "Statistic",
                ls.no AS "Results",
                p.player_name AS "Player Name",
                t.team_name AS "Team Name",
                y.year AS "Year"
            FROM last_5_ys_yealy_stats AS ls
            JOIN statistics AS s ON ls.statistic_id = s.statistic_id
            JOIN stat_titles AS st ON s.stat_title_id = st.stat_title_id
            JOIN players AS p ON ls.player_id = p.player_id
            JOIN teams AS t ON p.team_id = t.team_id
            JOIN years AS y ON ls.year_id = y.year_id
            JOIN leagues AS l ON ls.league_id = l.league_id
            WHERE l.league = :league 
              AND st.stat_title = :stat_title
              AND s.statistic = :statistic
        """)

        df = pd.read_sql(query, engine, params={
            'league': selected_league,
            'stat_title': selected_stat_title,
            'statistic': selected_statistic
        })
        
        if df.empty:
            st.warning("No data found for the selected filters.")
            return

        # Dinamic title
        st.subheader(f"Showing {selected_statistic} for {selected_league} - {selected_stat_title}")
        st.dataframe(df, use_container_width=True)

        df = df.dropna()

        # Ensure values are numeric
        df["Results"] = pd.to_numeric(df["Results"], errors='coerce')

        # Ensure Year is string and ordered
        df['Year'] = df['Year'].astype(str)
        year_order = sorted(df['Year'].unique(), key=int)
        df['Year'] = pd.Categorical(df['Year'], categories=year_order, ordered=True)

        # Create single bar trace
        fig = go.Figure(data=[
            go.Bar(
                x=df['Year'],
                y=df['Results'],
            )
        ])

        # Layout
        fig.update_layout(
            title={
                'text': f"{selected_statistic} for {selected_league} - {selected_stat_title}",
                'font': dict(size=20)
            },
            xaxis=dict(
                title='Years',
                type='category',
                categoryorder='array',
                categoryarray=year_order,
                tickmode='linear'
            ),
            yaxis=dict(
                title='Results'
            ),
            bargap=0.15,
            bargroupgap=0.05,
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Plot comparison chart
        # --- Pull both leagues explicitly for second chart ---
        league_query = text("""
            SELECT 
                l.league AS "League",
                y.year AS "Year",
                ls.no AS "Results"
            FROM last_5_ys_yealy_stats AS ls
            JOIN statistics AS s ON ls.statistic_id = s.statistic_id
            JOIN stat_titles AS st ON s.stat_title_id = st.stat_title_id
            JOIN years AS y ON ls.year_id = y.year_id
            JOIN leagues AS l ON ls.league_id = l.league_id
            WHERE st.stat_title = :stat_title
            AND s.statistic = :statistic
        """)

        df_leagues = pd.read_sql(league_query, engine, params={
            'stat_title': selected_stat_title,
            'statistic': selected_statistic
        })

        # Ensure clean data
        df_leagues["Year"] = pd.to_numeric(df_leagues["Year"], errors="coerce").astype(int)
        df_leagues["Results"] = pd.to_numeric(df_leagues["Results"], errors="coerce")
        df_leagues = df_leagues.dropna(subset=["Year", "Results", "League"])

        df_leagues = df_leagues.sort_values("Year")

        fig2 = px.line(
            df_leagues,
            x="Year",
            y="Results",
            color="League", 
            markers=True,
            title=f"American League and National League <br>{selected_stat_title} {selected_statistic} Over Time Compparison"
        )
        fig2.update_layout(
            height=500,
            title={
                'font': dict(size=20)
            },
            xaxis=dict(
                tickmode='linear',
                dtick=1  # Force every year to appear
            )
        )
        st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")

def top_25_players_ranked(engine):
    st.title("Best Players Ranked (2021-2024)")

    # Sidebar filters
    with st.sidebar:
        st.header("Ranking Filters")

        leagues = fetch_distinct_column_values(engine, "leagues", "league", fallback=["American League", "National League"])
        stat_titles = fetch_distinct_column_values(engine, "stat_titles", "stat_title", fallback=["Hitting Statistics", "Pitching Statistics"])

        league = st.radio("Select League", leagues)
        stat_title = st.radio("Select Statistic Group", stat_titles)

        fallback_stats = {
            "Hitting Statistics": ["Base on Balls", "Batting Average", "Doubles", "Hits", "Home Runs", "On Base Percentage", "RBI", "Runs", "Slugging Average", "Stolen Bases", "Total Bases", "Triples"],
            "Pitching Statistics": ["Complete Games", "ERA", "Games", "Saves", "Shutouts", "Strikeouts", "Winning Percentage", "Wins"]
        }
        statistic_options = fetch_statistics_by_title(engine, stat_title, fallback=fallback_stats.get(stat_title))
        statistic_name = st.selectbox("Choose Specific Statistic", statistic_options)

    try:
        query = text("""
            SELECT 
                p.player_name AS "Player Name",
                t.team_name AS "Team Name",
                ls.no AS "Results",
                s.statistic AS "Statistic",
                y.year AS "Year"
            FROM last_5_ys_yealy_stats AS ls
            JOIN statistics AS s ON ls.statistic_id = s.statistic_id
            JOIN stat_titles AS st ON s.stat_title_id = st.stat_title_id
            JOIN players AS p ON ls.player_id = p.player_id
            JOIN teams AS t ON p.team_id = t.team_id
            JOIN years AS y ON ls.year_id = y.year_id
            JOIN leagues AS l ON ls.league_id = l.league_id
            WHERE l.league = :league 
              AND st.stat_title = :stat_title 
              AND s.statistic = :statistic
            ORDER BY ls.no DESC
        """)

        df = pd.read_sql(query, engine, params={
            'league': league,
            'stat_title': stat_title,
            'statistic': statistic_name
        })

        #  Drop NAs
        df = df.dropna(subset=['Results'])
        # Show all decimals in 0.000 format without modifying actual values
        df['Results'] = df['Results'].apply(lambda x: f"{x:.3f}" if pd.notnull(x) else "")
        # Add rank column
        df['Rank'] = range(1, len(df) + 1)
        # Reorder columns
        df = df[['Rank', 'Player Name', 'Results', 'Year']]

        # Dinamic title
        st.subheader(f"Top 25 {statistic_name} in {league} - {stat_title} (2021-2024)")
        st.dataframe(df, use_container_width=True)

        # Query all player stats with team and year
        player_counts_query = text("""
            SELECT 
                p.player_name AS "Player Name",
                t.team_name AS "Team Name",
                ls.no AS "Results",
                s.statistic AS "Statistic",
                y.year AS "Year"
            FROM last_5_ys_yealy_stats AS ls
            JOIN players AS p ON ls.player_id = p.player_id
            JOIN teams AS t ON p.team_id = t.team_id
            JOIN statistics AS s ON ls.statistic_id = s.statistic_id
            JOIN stat_titles AS st ON s.stat_title_id = st.stat_title_id
            JOIN years AS y ON ls.year_id = y.year_id
            JOIN leagues AS l ON ls.league_id = l.league_id
        """)

        # Run the query (no params needed)
        player_counts = pd.read_sql(player_counts_query, engine)

        # Replace "To Be Determined" with NaN, then drop rows with NaN in 'Team Name'
        player_counts['Team Name'] = player_counts['Team Name'].replace("To Be Determined", np.nan)
        player_counts = player_counts.dropna()

        player_counts = (
            player_counts.groupby(['Team Name', 'Player Name'])
            .size()
            .reset_index(name='Count')
        )
        
        # Chart title
        st.subheader("Number of Times Each Player Was Best (2021–2024)")
        
        # Slider
        min_count = st.slider(
        "Minimum Wins per Player",
        min_value=1,
        max_value=int(player_counts['Count'].max()),
        value=st.session_state.get("min_count", 1),
        key="min_count"
    )

        # Filter data
        filtered_data = player_counts[player_counts['Count'] >= min_count]

        # Plot the chart
        fig = px.sunburst(
            filtered_data,
            path=['Team Name', 'Player Name'],
            values='Count'
        )
        fig.update_layout(
            width=700,
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching data: {e}")

# --- Main ---
if __name__ == "__main__":
    page = st.sidebar.selectbox("Choose Page", ["Yearly Best Results", "Best Players Ranked"])
    if page == "Yearly Best Results":
        get_statistics_by_league_stat_title(engine)
    else:
        top_25_players_ranked(engine)

    