
CREATE TABLE IF NOT EXISTS stat_titles (
    stat_title_id INTEGER PRIMARY KEY,
    stat_title TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS statistics (
    statistic_id INTEGER PRIMARY KEY,
    statistic TEXT NOT NULL,
    stat_title_id INTEGER NOT NULL,
    FOREIGN KEY (stat_title_id) REFERENCES stat_titles(stat_title_id)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS years (
    year_id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS leagues (
    league_id INTEGER PRIMARY KEY,
    league TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS last_5_ys_yearly_stats (
    statistic_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    no REAL,
    top_25 TEXT,
    year_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    FOREIGN KEY (statistic_id) REFERENCES statistics(statistic_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (year_id) REFERENCES years(year_id),
    FOREIGN KEY (league_id) REFERENCES leagues(league_id)
);
