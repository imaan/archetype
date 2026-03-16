import pytest
from httpx import ASGITransport, AsyncClient

from input_engine.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
