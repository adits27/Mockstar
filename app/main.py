import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import sessions, turns, users
from app.store import session_store

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 2 * 60 * 60
CLEANUP_INTERVAL_SECONDS = 5 * 60


async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        expired = session_store.purge_expired(SESSION_TTL_SECONDS)
        if expired:
            logger.info("Purged %d expired session(s): %s", len(expired), expired)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title="MockStar Speech API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(turns.router)
app.include_router(users.router)
