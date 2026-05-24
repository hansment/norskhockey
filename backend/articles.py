from backend.database import get_connection
from pydantic import BaseModel
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

router = APIRouter()

class Artikkel(BaseModel):
    title: str
    content: str
    author: str = "Redaksjonen"
    image_url: str = None
    published: int = 0

@router.get("/artikler")
def hent_artikler(side: int = 1, antall: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    
    offset = (side - 1) * antall
    
    rows = cursor.execute("""
        SELECT * FROM articles 
        WHERE published = 1 
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (antall, offset)).fetchall()
    
    totalt = cursor.execute(
        "SELECT COUNT(*) FROM articles WHERE published = 1"
    ).fetchone()[0]
    
    conn.close()
    return {
        "artikler": [dict(row) for row in rows],
        "totalt": totalt,
        "side": side,
        "sider": -(-totalt // antall)  # Runder opp
    }

@router.get("/artikler/{id}")
def hent_artikkel(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM articles WHERE id = ?", (id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Artikkel ikke funnet")
    return dict(row)

@router.get("/admin/artikler/alle")
def hent_alle_artikler(passord: str):
    if passord != os.getenv("ADMIN_PASSWORD"):
        raise HTTPException(status_code=401, detail="Ugyldig passord")
    
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM articles 
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/admin/artikler")
def opprett_artikkel(artikkel: Artikkel, passord: str):
    if passord != os.getenv("ADMIN_PASSWORD"):
        raise HTTPException(status_code=401, detail="Ugyldig passord")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO articles (title, content, image_url, author, created_at, updated_at, published)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        artikkel.title,
        artikkel.content,
        artikkel.image_url,
        artikkel.author,
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        artikkel.published
    ))
    conn.commit()
    conn.close()
    return {"message": "Artikkel opprettet"}

@router.put("/admin/artikler/{id}")
def oppdater_artikkel(id: int, artikkel: Artikkel, passord: str):
    if passord != os.getenv("ADMIN_PASSWORD"):
        raise HTTPException(status_code=401, detail="Ugyldig passord")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE articles 
        SET title = ?, content = ?, image_url = ?, author = ?, 
            updated_at = ?, published = ?
        WHERE id = ?
    """, (
        artikkel.title,
        artikkel.content,
        artikkel.image_url,
        artikkel.author,
        datetime.now().isoformat(),
        artikkel.published,
        id
    ))
    conn.commit()
    conn.close()
    return {"message": "Artikkel oppdatert"}

@router.delete("/admin/artikler/{id}")
def slett_artikkel(id: int, passord: str):
    if passord != os.getenv("ADMIN_PASSWORD"):
        raise HTTPException(status_code=401, detail="Ugyldig passord")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Artikkel slettet"}

@router.post("/admin/last-opp-bilde")
async def last_opp_bilde(passord: str, fil: UploadFile = File(...)):
    if passord != os.getenv("ADMIN_PASSWORD"):
        raise HTTPException(status_code=401, detail="Ugyldig passord")
    
    innhold = await fil.read()
    resultat = cloudinary.uploader.upload(innhold)
    return {"url": resultat["secure_url"]}