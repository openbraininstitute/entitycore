# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from app import models
from app.config import settings
from app.dependencies.db import get_db
from app.models.base import Base


@pytest.fixture(scope="function")
def client():
    engine = create_engine(settings.DB_URI)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        yield db
        db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client


@pytest.fixture(scope="function")
def db():
    engine = create_engine(settings.DB_URI, poolclass=StaticPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    return db


@pytest.fixture(scope="session", autouse=True)
def _db_int():
    models.init_db(settings.DB_URI)


@pytest.fixture(autouse=True)
def _db_cleanup(db):
    yield
    query = text(
        f"""TRUNCATE {",".join(Base.metadata.tables)} RESTART IDENTITY CASCADE"""
    )
    db.execute(query)
    db.commit()
