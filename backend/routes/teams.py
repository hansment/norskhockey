from fastapi import APIRouter
from backend.database import get_connection

router = APIRouter()

@router.get("/lag")
def hent_lag(divisjon: str = None):
    conn = get_connection()
    cursor = conn.cursor()

    if divisjon:
        rows = cursor.execute(
            "SELECT * FROM teams WHERE division = ?", (divisjon,)
        ).fetchall()
    else:
        rows = cursor.execute("SELECT * FROM teams").fetchall()

    conn.close()
    return [dict(row) for row in rows]

@router.get("/lag/{id}")
def hent_ett_lag(id: int):
    conn = get_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT * FROM teams WHERE id = ?", (id,)
    ).fetchone()

    conn.close()

    if row is None:
        return {"error": "Lag ikke funnet"}
    return dict(row)