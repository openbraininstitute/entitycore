import app.models
# Dependency to get the database session
def get_db():
    db = app.models.base.SessionLocal()
    try:
        yield db
    finally:
        db.close()
