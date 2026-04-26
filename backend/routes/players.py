from fastapi import APIRouter
from backend.database import get_connection

router = APIRouter()

@router.get("/spillere")
def hent_spillere(divisjon: str = None):
    conn = get_connection()
    cursor = conn.cursor()

    if divisjon:
        rows = cursor.execute("""
            SELECT 
                person_id,
                first_name,
                last_name,
                team_id,
                team_name,
                team_short_name,
                position,
                division,
                SUM(games_played)   as games_played,
                SUM(goals)          as goals,
                SUM(assists)        as assists,
                SUM(points)         as points,
                SUM(pim)            as pim,
                SUM(pp_goals)       as pp_goals,
                SUM(pp_assists)     as pp_assists,
                SUM(sh_goals)       as sh_goals,
                SUM(sh_assists)     as sh_assists,
                SUM(gwg)            as gwg,
                SUM(shots)          as shots,
                AVG(shot_pct)       as shot_pct,
                AVG(faceoff_win_pct) as faceoff_win_pct,
                MAX(ovr)            as ovr,
                MAX(last_updated)   as last_updated
            FROM players
            WHERE division = ?
            GROUP BY person_id, team_id
        """, (divisjon,)).fetchall()
    else:
        rows = cursor.execute("""
            SELECT 
                person_id,
                first_name,
                last_name,
                team_id,
                team_name,
                team_short_name,
                position,
                division,
                SUM(games_played)   as games_played,
                SUM(goals)          as goals,
                SUM(assists)        as assists,
                SUM(points)         as points,
                SUM(pim)            as pim,
                SUM(pp_goals)       as pp_goals,
                SUM(pp_assists)     as pp_assists,
                SUM(sh_goals)       as sh_goals,
                SUM(sh_assists)     as sh_assists,
                SUM(gwg)            as gwg,
                SUM(shots)          as shots,
                AVG(shot_pct)       as shot_pct,
                AVG(faceoff_win_pct) as faceoff_win_pct,
                MAX(ovr)            as ovr,
                MAX(last_updated)   as last_updated
            FROM players
            GROUP BY person_id, team_id
        """).fetchall()

    conn.close()
    return [dict(row) for row in rows]

@router.get("/spillere/{person_id}")
def hent_spiller(person_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT
            person_id,
            first_name,
            last_name,
            team_id,
            team_name,
            team_short_name,
            position,
            division,
            SUM(games_played)       as games_played,
            SUM(goals)              as goals,
            SUM(assists)            as assists,
            SUM(points)             as points,
            SUM(pim)                as pim,
            SUM(pp_goals)           as pp_goals,
            SUM(pp_assists)         as pp_assists,
            SUM(sh_goals)           as sh_goals,
            SUM(sh_assists)         as sh_assists,
            SUM(gwg)                as gwg,
            SUM(shots)              as shots,
            AVG(shot_pct)           as shot_pct,
            AVG(faceoff_win_pct)    as faceoff_win_pct,
            MAX(ovr)                as ovr,
            MAX(last_updated)       as last_updated
        FROM players
        WHERE person_id = ?
        GROUP BY person_id
    """, (person_id,)).fetchone()

    conn.close()

    if row is None:
        return {"error": "Spiller ikke funnet"}
    return dict(row)

@router.get("/spillere/{person_id}/per-lag")
def hent_spiller_per_lag(person_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT
            team_name,
            team_short_name,
            division,
            season,
            SUM(games_played)       as games_played,
            SUM(goals)              as goals,
            SUM(assists)            as assists,
            SUM(goals + assists)    as points,
            SUM(pim)                as pim,
            SUM(pp_goals)           as pp_goals,
            SUM(pp_assists)         as pp_assists,
            SUM(sh_goals)           as sh_goals,
            SUM(gwg)                as gwg,
            SUM(shots)              as shots,
            AVG(shot_pct)           as shot_pct,
            AVG(faceoff_win_pct)    as faceoff_win_pct,
            MAX(ovr)                as ovr
        FROM players
        WHERE person_id = ?
        GROUP BY team_id, season
        ORDER BY season DESC, games_played DESC
    """, (person_id,)).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@router.get("/keepere/{person_id}/per-lag")
def hent_keeper_per_lag(person_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT
            team_name,
            team_short_name,
            division,
            season,
            SUM(games_played)       as games_played,
            SUM(minutes_played)     as minutes_played,
            SUM(wins)               as wins,
            SUM(losses)             as losses,
            SUM(shutouts)           as shutouts,
            SUM(goals_against)      as goals_against,
            AVG(goals_against_avg)  as goals_against_avg,
            SUM(saves)              as saves,
            AVG(save_pct)           as save_pct,
            MAX(ovr)                as ovr
        FROM goalies
        WHERE person_id = ?
        GROUP BY team_id, season
        ORDER BY season DESC, games_played DESC
    """, (person_id,)).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@router.get("/sync/status")
def sync_status():
    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        "SELECT * FROM sync_log ORDER BY id DESC LIMIT 10"
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]

@router.get("/keepere")
def hent_keepere(divisjon: str = None):
    conn = get_connection()
    cursor = conn.cursor()

    if divisjon:
        rows = cursor.execute("""
            SELECT
                person_id,
                first_name,
                last_name,
                team_id,
                team_name,
                team_short_name,
                division,
                SUM(games_played)       as games_played,
                SUM(minutes_played)     as minutes_played,
                SUM(wins)               as wins,
                SUM(losses)             as losses,
                SUM(shutouts)           as shutouts,
                SUM(goals_against)      as goals_against,
                AVG(goals_against_avg)  as goals_against_avg,
                SUM(saves)              as saves,
                AVG(save_pct)           as save_pct,
                MAX(ovr)                as ovr,
                MAX(last_updated)       as last_updated
            FROM goalies
            WHERE division = ?
            GROUP BY person_id, team_id
        """, (divisjon,)).fetchall()
    else:
        rows = cursor.execute("""
            SELECT
                person_id,
                first_name,
                last_name,
                team_id,
                team_name,
                team_short_name,
                division,
                SUM(games_played)       as games_played,
                SUM(minutes_played)     as minutes_played,
                SUM(wins)               as wins,
                SUM(losses)             as losses,
                SUM(shutouts)           as shutouts,
                SUM(goals_against)      as goals_against,
                AVG(goals_against_avg)  as goals_against_avg,
                SUM(saves)              as saves,
                AVG(save_pct)           as save_pct,
                MAX(ovr)                as ovr,
                MAX(last_updated)       as last_updated
            FROM goalies
            GROUP BY person_id, team_id
        """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@router.get("/keepere/{person_id}")
def hent_keeper(person_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT
            person_id,
            first_name,
            last_name,
            team_id,
            team_name,
            team_short_name,
            division,
            SUM(games_played)       as games_played,
            SUM(minutes_played)     as minutes_played,
            SUM(wins)               as wins,
            SUM(losses)             as losses,
            SUM(shutouts)           as shutouts,
            SUM(goals_against)      as goals_against,
            AVG(goals_against_avg)  as goals_against_avg,
            SUM(saves)              as saves,
            AVG(save_pct)           as save_pct,
            MAX(ovr)                as ovr,
            MAX(last_updated)       as last_updated
        FROM goalies
        WHERE person_id = ?
        GROUP BY person_id
    """, (person_id,)).fetchone()

    conn.close()

    if row is None:
        return {"error": "Keeper ikke funnet"}
    return dict(row)