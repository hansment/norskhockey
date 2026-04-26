import requests
import time
from datetime import datetime
from backend.database import get_connection
from apscheduler.schedulers.blocking import BlockingScheduler

BASE_URL = "https://sf34-terminlister-prod-app.azurewebsites.net"
SPORT_ID = 152  # Ishockey



def hent_sesong_ar():
    now = datetime.now()
    return now.year if now.month >= 9 else now.year - 1

def hent_sesong_streng():
    ar = hent_sesong_ar()
    return f"{ar}/{ar + 1}"

def hent_sesong_id():
    year = hent_sesong_ar()
    response = requests.get(f"{BASE_URL}/ta/Seasons/?sportId=152&year={year}")
    data = response.json()
    return data["seasons"][0]["seasonId"]

def hent_tournament_ids():
    sesong_id = hent_sesong_id()
    response = requests.get(f"{BASE_URL}/ta/Tournament/Season/{sesong_id}")
    data = response.json()
    
    ids = {
        "EHL": [],
        "HL1": []
    }

    for t in data["tournamentsInSeason"]:
        no = t["tournamentNo"]
        
        if not t["areStatisticsPublished"]:
            continue

        if t["division"] == 0 and no.startswith("1200") and not no.endswith("09"):
            ids["EHL"].append(t["tournamentId"])
        elif t["division"] == 1 and no.startswith("1201") and not no.endswith("09") and not no.endswith("08") and no != "120103":
            ids["HL1"].append(t["tournamentId"])

    return ids


def er_sesong_aktiv():
    sesong_id = hent_sesong_id()
    response = requests.get(f"{BASE_URL}/ta/Tournament/Season/{sesong_id}")
    data = response.json()

    for s in data["tournamentsInSeason"]:
        if s["tournamentName"] == "EHL":
            if s["isArchival"]:
                return False
            fra = datetime.fromisoformat(s["fromDate"])
            til = datetime.fromisoformat(s["toDate"])
            today = datetime.now()
            return fra <= today <= til


def logg(status, message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sync_log (
            timestamp, status, message
        ) VALUES (?, ?, ?)
    """, (
        datetime.now().isoformat(),
        status,
        message
    ))
    cursor.execute("""
    DELETE FROM sync_log WHERE id NOT IN (
        SELECT id FROM sync_log ORDER BY id DESC LIMIT 100
    )
    """)

    conn.commit()
    conn.close()


def hent_lag(cursor):
    sesong = hent_sesong_streng()

    for divisjon, tournament_ids in hent_tournament_ids().items():
        for tournament_id in tournament_ids:
            response = requests.get(f"{BASE_URL}/ta/TournamentTeams/?tournamentId={tournament_id}")
            data = response.json()
            
            if "error" in data or "teams" not in data:
                continue

            for lag in data["teams"]:
                cursor.execute("""
                    INSERT OR REPLACE INTO teams (
                        id, name, logo, division, season, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    lag["teamId"],
                    lag["team"].strip(),
                    None,
                    divisjon,
                    sesong,
                    datetime.now().isoformat()
                ))


def hent_spillere(cursor):
    sesong = hent_sesong_streng()

    for divisjon, tournament_ids in hent_tournament_ids().items():
        for tournament_id in tournament_ids:

            response = requests.get(f"{BASE_URL}/wise/tournaments/{tournament_id}/players/statistics")
            data = response.json()

            if not isinstance(data, list):
                continue

            for spiller in data:
                cursor.execute("""
                    INSERT OR REPLACE INTO players (
                        person_id, first_name, last_name, team_id, team_name, team_short_name,
                        position, division, tournament_id, games_played, goals, assists, points, pim,
                        pp_goals, pp_assists, sh_goals, sh_assists, gwg, shots, shot_pct,
                        faceoffs, faceoff_win_pct, season, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    spiller["personId"],
                    spiller["firstName"],
                    spiller["lastName"],
                    spiller["orgId"],
                    spiller["teamName"],
                    spiller["teamShortName"],
                    spiller["position"],
                    divisjon,
                    tournament_id,
                    spiller["gamesPlayed"],
                    spiller["goalsScored"],
                    spiller["assists"],
                    spiller["points"],
                    spiller["pim"],
                    spiller["powerPlayGoals"],
                    spiller["powerPlayGoalAssists"],
                    spiller["shortHandedGoals"],
                    spiller["shortHandedGoalAssists"],
                    spiller["gwg"],
                    spiller["shots"],
                    spiller["shotsPct"],
                    spiller["faceOffs"],
                    spiller["faceoffsWinPct"],
                    sesong,
                    datetime.now().isoformat()
                ))

            time.sleep(5)  # Vær hensynsfull mot serveren

def hent_keepere(cursor):
    sesong = hent_sesong_streng()

    for divisjon, tournament_ids in hent_tournament_ids().items():
        for tournament_id in tournament_ids:

            response = requests.get(f"{BASE_URL}/wise/tournaments/{tournament_id}/goalies/statistics")
            data = response.json()

            if not isinstance(data, list):
                continue

            for keeper in data:
                cursor.execute("""
                    INSERT OR REPLACE INTO goalies (
                        person_id, first_name, last_name, team_id, team_name, team_short_name,
                        division, tournament_id, games_played, minutes_played, wins, losses, shutouts,
                        goals_against, goals_against_avg, saves, save_pct, season, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    keeper["personId"],
                    keeper["firstName"],
                    keeper["lastName"],
                    keeper["orgId"],
                    keeper["teamName"],
                    keeper["teamShortName"],
                    divisjon,
                    tournament_id,
                    keeper["gamesPlayed"],
                    keeper["minutesPlayed"],
                    keeper["wins"],
                    keeper["losses"],
                    keeper["so"],
                    keeper["ga"],
                    keeper["gaa"],
                    keeper["sv"],
                    keeper["svPct"],
                    sesong,
                    datetime.now().isoformat()
                ))

            time.sleep(5)  # Vær hensynsfull mot serveren


def normaliser(verdi, min_val, max_val):
    if max_val == min_val:
        return 50.0
    normalisert = (verdi - min_val) / (max_val - min_val)
    return round(30 + normalisert * 62, 1)

def beregn_rating(cursor):
    # Hent summert statistikk per spiller per lag
    spillere = cursor.execute("""
        SELECT 
            person_id,
            team_id,
            season,
            first_name,
            last_name,
            position,
            division,
            SUM(games_played)       as games_played,
            SUM(goals)              as goals,
            SUM(assists)            as assists,
            SUM(pp_goals)           as pp_goals,
            SUM(pp_assists)         as pp_assists,
            SUM(sh_goals)           as sh_goals,
            SUM(gwg)                as gwg,
            SUM(shots)              as shots,
            AVG(shot_pct)           as shot_pct,
            AVG(faceoff_win_pct)    as faceoff_win_pct
        FROM players
        GROUP BY person_id, team_id, season
        HAVING games_played >= 5
    """).fetchall()

    for spiller in spillere:
        gp = spiller["games_played"]
        posisjon = spiller["position"]

        mål_pk       = spiller["goals"] / gp
        assists_pk   = spiller["assists"] / gp
        poeng_pk     = (spiller["goals"] + spiller["assists"]) / gp
        pp_poeng_pk  = (spiller["pp_goals"] + spiller["pp_assists"]) / gp
        gwg_pk       = spiller["gwg"] / gp
        sh_mål_pk    = spiller["sh_goals"] / gp
        skuddprosent = spiller["shot_pct"] or 0
        faceoff_pct  = spiller["faceoff_win_pct"] or 0.5

        if posisjon in ("LW", "RW", "CE"):
            råscore = (
                poeng_pk     * 0.30 +
                mål_pk       * 0.20 +
                skuddprosent * 0.15 +
                pp_poeng_pk  * 0.15 +
                gwg_pk       * 0.10 +
                faceoff_pct  * 0.05 +
                sh_mål_pk    * 0.05
            )
        elif posisjon in ("LD", "RD"):
            råscore = (
                assists_pk  * 0.25 +
                pp_poeng_pk * 0.20 +
                gwg_pk      * 0.20 +
                faceoff_pct * 0.20 +
                poeng_pk    * 0.10 +
                sh_mål_pk   * 0.05
            )
        else:
            råscore = (
                poeng_pk    * 0.35 +
                mål_pk      * 0.20 +
                faceoff_pct * 0.20 +
                gwg_pk      * 0.15 +
                sh_mål_pk   * 0.10
            )

        division_factor  = 1.0 if spiller["division"] == "EHL" else 0.90
        råscore         *= division_factor

        cursor.execute("""
            UPDATE players SET ovr = ?
            WHERE person_id = ? AND team_id = ? AND season = ?
        """, (råscore, spiller["person_id"], spiller["team_id"], spiller["season"]))

    # Normaliser spillere
    rader = cursor.execute("""
        SELECT person_id, team_id, season, ovr, SUM(games_played) as games_played
        FROM players WHERE ovr IS NOT NULL
        GROUP BY person_id, team_id, season
    """).fetchall()
    verdier = [r["ovr"] for r in rader]
    if verdier:
        min_val = min(verdier)
        max_val = max(verdier)
        for rad in rader:
            normalisert = normaliser(rad["ovr"], min_val, max_val)
            reliability = min(rad["games_played"] / 20, 1.0)
            endelig = round(30 + (normalisert - 30) * reliability, 1)
            cursor.execute(
                "UPDATE players SET ovr = ? WHERE person_id = ? AND team_id = ? AND season = ?",
                (endelig, rad["person_id"], rad["team_id"], rad["season"])
            )

    # Keepere
    keepere = cursor.execute("""
        SELECT
            person_id,
            team_id,
            season,
            division,
            SUM(games_played)       as games_played,
            SUM(minutes_played)     as minutes_played,
            SUM(wins)               as wins,
            SUM(shutouts)           as shutouts,
            SUM(goals_against)      as goals_against,
            SUM(saves)              as saves,
            AVG(save_pct)           as save_pct,
            AVG(goals_against_avg)  as goals_against_avg
        FROM goalies
        GROUP BY person_id, team_id, season
        HAVING games_played >= 5
    """).fetchall()

    for keeper in keepere:
        gp = keeper["games_played"]

        redningsprosent = keeper["save_pct"] or 0
        gaa             = keeper["goals_against_avg"] or 0
        vinnerprosent   = keeper["wins"] / gp
        nullet_pk       = keeper["shutouts"] / gp

        råscore = (
            redningsprosent * 0.40 +
            (1 / (gaa + 1)) * 0.30 +
            vinnerprosent   * 0.20 +
            nullet_pk       * 0.10
        )

        division_factor = 1.0 if keeper["division"] == "EHL" else 0.90
        råscore        *= division_factor

        cursor.execute("""
            UPDATE goalies SET ovr = ?
            WHERE person_id = ? AND team_id = ? AND season = ?
        """, (råscore, keeper["person_id"], keeper["team_id"], keeper["season"]))

    # Normaliser keepere
    rader = cursor.execute("""
        SELECT person_id, team_id, season, ovr, SUM(games_played) as games_played
        FROM goalies WHERE ovr IS NOT NULL
        GROUP BY person_id, team_id, season
    """).fetchall()
    verdier = [r["ovr"] for r in rader]
    if verdier:
        min_val = min(verdier)
        max_val = max(verdier)
        for rad in rader:
            normalisert = normaliser(rad["ovr"], min_val, max_val)
            reliability = min(rad["games_played"] / 20, 1.0)
            endelig = round(30 + (normalisert - 30) * reliability, 1)
            cursor.execute(
                "UPDATE goalies SET ovr = ? WHERE person_id = ? AND team_id = ? AND season = ?",
                (endelig, rad["person_id"], rad["team_id"], rad["season"])
            )

def synk_alt():
    if not er_sesong_aktiv():
        logg("SKIPPED", "Ingen aktiv sesong")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        hent_lag(cursor)
        hent_spillere(cursor)
        hent_keepere(cursor)
        beregn_rating(cursor)
        conn.commit()
        logg("SUCCESS", "Synkronisering fullført")
    except Exception as e:
        conn.rollback()
        logg("ERROR", str(e))
    finally:
        conn.close()


scheduler = BlockingScheduler()

scheduler.add_job(synk_alt, 'cron', day_of_week='sun,mon,tue', hour=2, minute=0)

if __name__ == "__main__":
    synk_alt()
    print("Scheduler startet - venter på neste kjøring...")
    scheduler.start()
