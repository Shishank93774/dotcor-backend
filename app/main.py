from contextlib import asynccontextmanager

import app.db.models
import app.schemas
from app.db.connection import Base, engine, get_db
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: run once when application starts
    print("Application started")

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    yield  # This allows the application to run

    # Shutdown logic: run once when application stops
    print("Application stopped")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    return JSONResponse(content={"message": "Hello, World!"}, status_code=200)


@app.get("/db-test")
async def db_test(db: Session = Depends(get_db)):
    # Test database connection by executing a simple query
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return JSONResponse(
            content={"message": "Database connection successful", "result": result},
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(
            content={"message": "Database connection failed", "error": str(e)},
            status_code=500,
        )
