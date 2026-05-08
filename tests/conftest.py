import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.store import session_store


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def clear_store():
    session_store.clear()
    yield
    session_store.clear()
