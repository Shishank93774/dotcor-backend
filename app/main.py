from contextlib import asynccontextmanager

import app.db.models
import app.schemas
from app.api.v1.booking import router as booking_router
from app.api.v1.doctor import router as doctor_router
from app.api.v1.patient import router as patient_router
from app.api.v1.slot import router as slot_router
from app.core.exceptions import setup_exception_handlers
from app.core.logging import get_logger
from app.db.connection import Base, engine, get_db
from fastapi import Depends, FastAPI, status
from sqlalchemy import text
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: run once when application starts
    logger = get_logger(__name__)

    logger.info("Application started")

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    yield  # This allows the application to run

    # Shutdown logic: run once when application stops
    logger.info("Application stopped")


app = FastAPI(lifespan=lifespan)

setup_exception_handlers(app)


@app.get("/", status_code=status.HTTP_200_OK)
async def home():
    return {"message": "Hello, World!"}


@app.get("/db-test", status_code=status.HTTP_200_OK)
async def db_test(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"message": "Database connection successful", "result": result}


app.include_router(patient_router)
app.include_router(doctor_router)
app.include_router(booking_router)
app.include_router(slot_router)
