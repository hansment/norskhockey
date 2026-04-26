from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import init_db
from backend import sync
from backend.routes.players import router as players_router
from backend.routes.teams import router as teams_router
import threading

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    thread = threading.Thread(target=sync.scheduler.start, daemon=True)
    thread.start()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(players_router)
app.include_router(teams_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hockey Stats API kjører!"}

@app.get("/admin/sync")
def manuell_sync():
    thread = threading.Thread(target=lambda: sync.synk_alt(force=True))
    thread.start()
    return {"message": "Synkronisering startet i bakgrunnen"}
