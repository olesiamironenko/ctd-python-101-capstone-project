import sqlite3

def get_connection():
    try:
        return sqlite3.connect(".db/basebal_stats.db")
    except sqlite3.Error as e:
        print(f"Error connecting to DB: {e}")
        return None
    
def show_menu():
    print("\n What do you want to know:")
    print("1. One year statistics within last 5 years")
    print("2. Teams with top 25 players")
    print("3. Teams with top 25 players")
    print("4. League vs league performance for choosen year")
    print("5. Exit")

def query_one_year_statistics(conn):
    try:
        year = input("Enter year (any from 2021 to 2025): ").strip()
        year = input("Enter league (A for American League, N for National League): ").strip()
        cursor = conn.execute("""SELECT 
        stat_titles.stat_title,
        statistics.statistic,
        last_5_ys_yearly_stats.no, 
        leagues.league, 
        teams.team_name,
        players.player_name
            FROM last_5_ys_yearly 
            WHERE years.year = ? and leagues.league = ?
            ORDER BY last_5_ys_yearly_stats.no DESC""", (year,))
        results = cursor.fetchall()
        if results:
            print(f"\nTop hitters in {year}:")
            for row in results:
                print(f"{row[0]} ({row[1]}) - AVG: {row[2]}")
        else:
            print("No results found.")
    except Exception as e:
        print(f"Error: {e}")

def query_avg_threshold(conn):
    try:
        threshold = float(input("Enter AVG threshold (e.g., 0.35): ").strip())
        cursor = conn.execute("SELECT year, player, avg FROM batting_avg_leaders WHERE avg >= ? ORDER BY avg DESC", (threshold,))
        results = cursor.fetchall()
        if results:
            print(f"\nPlayers with AVG ≥ {threshold}:")
            for row in results:
                print(f"{row[1]} ({row[0]}) - AVG: {row[2]}")
        else:
            print("No players found.")
    except Exception as e:
        print(f"Error: {e}")
def query_team(conn):
    try:
        team = input("Enter team name (e.g., Miami): ").strip()
        cursor = conn.execute("SELECT year, player, avg FROM batting_avg_leaders WHERE team LIKE ? ORDER BY year DESC", (f"%{team}%",))
        results = cursor.fetchall()
        if results:
            print(f"\nPlayers from {team}:")
            for row in results:
                print(f"{row[1]} ({row[0]}) - AVG: {row[2]}")
        else:
            print("No players found.")
    except Exception as e:
        print(f"Error: {e}")
def main():
    conn = get_connection()
    if not conn:
        return
    try:
        while True:
            show_menu()
            choice = input("Choice: ").strip()
            if choice == "1":
                query_top_hitters_by_year(conn)
            elif choice == "2":
                query_avg_threshold(conn)
            elif choice == "3":
                query_team(conn)
            elif choice == "4":
                print("Goodbye.")
                break
            else:
                print("Invalid option.")
    finally:
        conn.close()
if __name__ == "__main__":
    main()