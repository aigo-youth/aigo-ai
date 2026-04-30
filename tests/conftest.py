import os
import pytest

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("SERVICE_KEY", "test-secret")

@pytest.fixture
def client():
  from fastapi.testclient import TestClient
  from app.main import app
  
  with TestClient(app) as test_client:
    yield test_client