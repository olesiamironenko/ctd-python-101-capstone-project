import pandas as pd
from sqlalchemy import create_engine, text

def get_statistics_by_league_year_stat_title(engine):
    # Ask user for inputs
    league = input("Enter league name ('American League' or 'National League'): ").strip()
    year = input("Enter year (choose one from 2021 to 2025): ").strip()
    stat_title = input("Enter statistic group ('Hitting Statistics' or 'Pitching Statistics'): ").strip()
    sort_column = input("Sort by column (choose one: 'no', 'player_name', 'team_name', 'statistic'): ").strip()
    sort_order = input("Sort order ('asc' or 'desc'): ").strip().lower()

    # Validate inputs
    if sort_order not in ('asc', 'desc'):
        print("Invalid sort order. Defaulting to 'desc'.")
        sort_order = 'desc'

    allowed_leagues = ['American League', 'National League']
    if league not in allowed_leagues:
        print(f"Invalid league. Defaulting to '{allowed_leagues[0]}'.")
        league = allowed_leagues[0]  # ✅ Fixed

    allowed_years = ['2021', '2022', '2023', '2024', '2025']
    if year not in allowed_years:
        print(f"Invalid year. Defaulting to '{allowed_years[0]}'.")
        year = allowed_years[0]

    allowed_titles = ['Hitting Statistics', 'Pitching Statistics']
    if stat_title not in allowed_titles:
        print(f"Invalid statistic group. Defaulting to '{allowed_titles[0]}'.")
        stat_title = allowed_titles[0]

    allowed_sort_columns = ['no', 'player_name', 'team_name', 'statistic']
    if sort_column not in allowed_sort_columns:
        print(f"Invalid sort column. Defaulting to 'no'.")
        sort_column = 'no'

    query = text(f"""
        SELECT 
            s.statistic AS "Statistic",
            ls.no AS "Results",
            p.player_name AS "Player Name",
            t.team_name AS "Team Name"
        FROM last_5_ys_yealy_stats AS ls
        JOIN statistics AS s ON ls.statistic_id = s.statistic_id
        JOIN stat_titles AS st ON s.stat_title_id = st.stat_title_id
        JOIN players AS p ON ls.player_id = p.player_id
        JOIN teams AS t ON p.team_id = t.team_id
        JOIN years AS y ON ls.year_id = y.year_id
        JOIN leagues AS l ON ls.league_id = l.league_id
        WHERE l.league = :league AND y.year = :year AND st.stat_title = :stat_title
        ORDER BY {sort_column} {sort_order.upper()};
    """)

    df = pd.read_sql(query, engine, params={
        'league': league,
        'year': int(year),
        'stat_title': stat_title
    })

    return df, league, year, stat_title

def main():
    engine = create_engine('sqlite:///db/baseball_stats.db')

    # Fetch stats by user inputs
    result = get_statistics_by_league_year_stat_title(engine)
    if result:
        df, league, year, stat_title = result
        if not df.empty:
            print("\n Top 25 Player Statistics Based on Your Selection:")
            print(f"    {stat_title} - {league}, {year}:\n")
            print(df)
        else:
            print("\nNo results found for the given filters.")

if __name__ == "__main__":
    main()