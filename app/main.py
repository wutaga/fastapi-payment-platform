from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.api.v1.payments import router as payments_router

app = FastAPI()

app.include_router(payments_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1")).scalar()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Service unavailable") from exc
    return {"database": "ok"}

