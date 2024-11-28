import models
# Dependency to get the database session
def get_db():
    db = models.base.SessionLocal()
    try:
        yield db
    finally:
        db.close()
