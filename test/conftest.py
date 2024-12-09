# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.dependencies.db import get_db
from app.config import TEST_DATABASE_URI
from sqlalchemy.pool import StaticPool
from app.models.base import Base
from fastapi.testclient import TestClient
from app import app

@pytest.fixture(scope="function")
def client():
    engine = create_engine(
        TEST_DATABASE_URI,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        yield db
        db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client

@pytest.fixture(scope="function")
def db():
    engine = create_engine(TEST_DATABASE_URI, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    return db
