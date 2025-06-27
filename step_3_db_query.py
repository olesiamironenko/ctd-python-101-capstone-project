import pandas as pd
from sqlalchemy import create_engine, text

def get_statistics_by_league_year_stat_title(engine):
    try:
        # Ask user for inputs
        year = input("Enter year (choose one from 2021 to 2025): ").strip()
        league = input("Enter league name ('American League' or 'National League'): ").strip()
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
            league = allowed_leagues[0]

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
            print(f"Invalid sort column. Defaulting to 'statistic'.")
            sort_column = 'statistic'

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
            'year': int(year),
            'league': league,
            'stat_title': stat_title
        })

        return df, year, league, stat_title
    
    except Exception as e:
        print(f"{e}")

def top_25_players_ranked(engine):
    try:
        # Choices
        # allowed_years = ['2021', '2022', '2023', '2024', '2025']
        allowed_leagues = ['American League', 'National League']
        allowed_titles = ['Hitting Statistics', 'Pitching Statistics']

        # Statistic mapping
        statistics_by_title = {
            0: [  # Hitting
                (0, 'Base on Balls'), (1, 'Batting Average'), (3, 'Doubles'),
                (6, 'Hits'), (7, 'Home Runs'), (8, 'On Base Percentage'),
                (9, 'RBI'), (10, 'Runs'), (13, 'Slugging Average'),
                (14, 'Stolen Bases'), (16, 'Total Bases'), (17, 'Triples')
            ],
            1: [  # Pitching
                (2, 'Complete Games'), (4, 'ERA'), (5, 'Games'),
                (11, 'Saves'), (12, 'Shutouts'), (15, 'Strikeouts'),
                (18, 'Winning Percentage'), (19, 'Wins')
            ]
        }
        stat_title_id_map = {'Hitting Statistics': 0, 'Pitching Statistics': 1}

        # Ask user for inputs
        print("\nAvailable Leagues:")
        for i, league in enumerate(allowed_leagues, start=1):
            print(f"{i}. {league}")
        league = input("Enter league name: ").strip()
        if league not in allowed_leagues:
            print(f"Invalid league. Defaulting to {allowed_leagues[0]}")
            league = allowed_leagues[0]

        print("\nStatistic Groups:")
        for title in allowed_titles:
            print(f"- {title}")
        stat_title = input("Enter statistic group: ").strip()
        if stat_title not in allowed_titles:
            print(f"Invalid group. Defaulting to {allowed_titles[0]}")
            stat_title = allowed_titles[0]
        stat_title_id = stat_title_id_map[stat_title]

        print("\nChoose a specific statistic:")
        stats_list = statistics_by_title[stat_title_id]
        for i, (_, stat) in enumerate(stats_list, start=1):
            print(f"{i}. {stat}")
        while True:
            choice = input("Enter number of statistic: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(stats_list):
                _, statistic_name = stats_list[int(choice) - 1]
                break
            else:
                print("Invalid choice, try again.")

        query = text(f"""
            SELECT 
                p.player_name AS "Player Name",
                ls.no AS "Results",
                s.statistic AS "Statistic",
                y.year AS "Year"
            FROM last_5_ys_yealy_stats AS ls
            JOIN statistics AS s ON ls.statistic_id = s.statistic_id
            JOIN stat_titles AS st ON s.stat_title_id = st.stat_title_id
            JOIN players AS p ON ls.player_id = p.player_id
            JOIN years AS y ON ls.year_id = y.year_id
            JOIN leagues AS l ON ls.league_id = l.league_id
            WHERE l.league = :league AND st.stat_title = :stat_title AND s.statistic = :statistic
            ORDER BY ls.no DESC;
        """)

        df = pd.read_sql(query, engine, params={
            'league': league,
            'stat_title': stat_title,
            'statistic': statistic_name
        })

        # Drop rows with NaN in 'Results'
        df = df.dropna(subset=['Results'])

        # Add ascending ranks (1, 2, 3...) to descending 'Results'
        df['Rank'] = range(1, len(df) + 1)

        # Optional: reorder columns
        df = df[['Rank', 'Player Name', 'Results', 'Year']]

        return df, league, stat_title, statistic_name
    
    except Exception as e:
        print(f"{e}")

def all_top_25_players_2021_2025(engine):
    try:
        query = text(f"""
            SELECT 
                l.league AS "League",
                t.team_name AS "Team Name",
                p.player_name AS "Player Name"
            FROM last_5_ys_yealy_stats AS ls
            JOIN players AS p ON ls.player_id = p.player_id
            JOIN teams AS t ON p.team_id = t.team_id
            JOIN leagues AS l ON ls.league_id = l.league_id
            GROUP BY t.team_name, p.player_name
            ORDER BY t.team_name, p.player_name DESC
        """)

        df = pd.read_sql(query, engine)

        return df

    except Exception as e:
        print(f"{e}")

def top_25_players_per_team_2021_2025(engine):
    try:
        query = text(f"""
            SELECT 
                l.league AS "League",
                t.team_name AS "Team Name",
                COUNT(DISTINCT p.player_id) AS "Number of Top 25 Players"
            FROM last_5_ys_yealy_stats AS ls
            JOIN players AS p ON ls.player_id = p.player_id
            JOIN teams AS t ON p.team_id = t.team_id
            JOIN leagues AS l ON ls.league_id = l.league_id
            GROUP BY t.team_name
            ORDER BY "Number of Top 25 Players" DESC
        """)

        df = pd.read_sql(query, engine)

        return df

    except Exception as e:
        print(f"{e}")

def main():
    engine = create_engine('sqlite:///db/baseball_stats.db')

    while True:
        print("\nMenu:")
        print("1. One year statistics")
        print("2. Top 25 players ranked")
        print("3. All top 25 players from 2021 to 2025")
        print("4. Number of top 25 Players per taem from 2021 to 2025")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':

            # Fetch stats by user inputs
            result = get_statistics_by_league_year_stat_title(engine)
            if result:
                df, league, year, stat_title = result
                if not df.empty:
                    print("\n Top 25 Player Statistics Based on Your Selection:")
                    print(f"    {stat_title} - {league}, {year}:\n")
                    print(df)
                else:
                    print("\n No results found for the given filters.")

        elif choice == '2':

            # Fetch ranked players by user inputs
            result = top_25_players_ranked(engine)
            if result:
                df, league, stat_title, statistic_name = result
                if not df.empty:
                    print("\n Top 25 Players from 2021 to 2025 ranked:")
                    print(f"    {statistic_name} in {stat_title}, {league}:\n")
                    print(df)
                else:
                    print("\n No results found for the given filters.")
 
        elif choice == '3':

            # Fetch list of players, no user input needed
            df = all_top_25_players_2021_2025(engine)
            if df is not None:
                if not df.empty:
                    print("\n All top 25 Players from 2021 to 2025:")
                    print(df)
                else:
                    print("\n No results found for the given filters.")

        elif choice == '4':
            df = top_25_players_per_team_2021_2025(engine)
            if df is not None:
                if not df.empty:
                    print("\n Number of top 25 Players per taem from 2021 to 2025:")
                    print(df)
                else:
                    print("\n No results found for the given filters.")

        elif choice == '5':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()