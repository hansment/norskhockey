import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hockey.db")

def get_connection():
    """Åpner en tilkobling til databasen"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Oppretter alle tabeller hvis de ikke finnes fra før"""
    conn = get_connection()
    cursor = conn.cursor()

    # Lag-tabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id              INTEGER PRIMARY KEY,
            name            TEXT NOT NULL,
            logo            TEXT,
            division        TEXT,
            season          TEXT,
            last_updated    TEXT
        )
    """)

    # Feltspiller-tabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            person_id           INTEGER,
            first_name          TEXT,
            last_name           TEXT,
            ovr                 REAL,
            team_id             INTEGER,
            team_name           TEXT,
            team_short_name     TEXT,
            position            TEXT,
            division            TEXT,
            games_played        INTEGER,
            goals               INTEGER,
            assists             INTEGER,
            points              INTEGER,
            pim                 INTEGER,
            pp_goals            INTEGER,
            pp_assists          INTEGER,
            sh_goals            INTEGER,
            sh_assists          INTEGER,
            gwg                 INTEGER,
            shots               INTEGER,
            shot_pct            REAL,
            faceoffs            INTEGER,
            faceoff_win_pct     REAL,
            tournament_id       INTEGER,
            season              TEXT,
            last_updated        TEXT,
            PRIMARY KEY (person_id, team_id, tournament_id, season)
        )
    """)

    # Keeper-tabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goalies (
            person_id           INTEGER,
            first_name          TEXT,
            last_name           TEXT,
            ovr                 REAL,
            team_id             INTEGER,
            team_name           TEXT,
            team_short_name     TEXT,
            division            TEXT,
            games_played        INTEGER,
            minutes_played      INTEGER,
            wins                INTEGER,
            losses              INTEGER,
            shutouts            INTEGER,
            goals_against       INTEGER,
            goals_against_avg   REAL,
            saves               INTEGER,
            save_pct            REAL,
            tournament_id       INTEGER,
            season              TEXT,
            last_updated        TEXT,
            PRIMARY KEY (person_id, team_id, tournament_id, season)
        )
    """)

    # Sync-status tabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_status (
            id              INTEGER PRIMARY KEY DEFAULT 1,
            last_synced     TEXT,
            tournament_id   INTEGER
        )
    """)

    # Artikkel-tabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            image_url   TEXT,
            author      TEXT,
            created_at  TEXT,
            updated_at  TEXT,
            published   INTEGER DEFAULT 0
        )
    """)

    # Sync-log tabell
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT,
            status          TEXT,
            message         TEXT
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO sync_status (id)
        VALUES (1)
    """)

    conn.commit()
    conn.close()
    print("Database initialisert OK")

if __name__ == "__main__":
    init_db()