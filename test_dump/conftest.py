# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.application import app
from app.config import LEGACY_TEST_DATABASE_URI, LEGACY_DATABASE_CONNECT_ARGS
from app.dependencies.db import get_db
from app.db.model import Base


@pytest.fixture(scope="function")
def client():
    engine = create_engine(
        LEGACY_TEST_DATABASE_URI,
        connect_args=LEGACY_DATABASE_CONNECT_ARGS,
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
    engine = create_engine(
        LEGACY_TEST_DATABASE_URI,
        connect_args=LEGACY_DATABASE_CONNECT_ARGS,
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    return db
