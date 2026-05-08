from fastapi import FastAPI
from app.routers import sessions, turns

app = FastAPI(title="MockStar Speech API")
app.include_router(sessions.router)
app.include_router(turns.router)
