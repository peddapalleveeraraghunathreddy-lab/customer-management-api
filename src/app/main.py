from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db

app = FastAPI(title="Customer Management API")

@app.get("/health")
def health(db: Session = Depends(get_db)):
    return {
        "status": "healthy",
        "database": "configured"
    }