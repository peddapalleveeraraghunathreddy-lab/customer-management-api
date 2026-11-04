
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from src.app.database import get_db
from src.app.models import Customer
from src.app.schemas import CustomerCreate, CustomerUpdate, CustomerOut

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Customer Management API")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    expected_api_key = os.getenv("API_KEY")

    if not expected_api_key or api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    return api_key


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "configured"}


@app.post(
    "/customers",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
def create_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    existing_customer = (
        db.query(Customer)
        .filter(Customer.email == customer_data.email)
        .first()
    )

    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    new_customer = Customer(**customer_data.model_dump())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@app.get(
    "/customers",
    response_model=list[CustomerOut],
    dependencies=[Depends(verify_api_key)],
)
def get_customers(
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db),
):
    if page < 1 or per_page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page and per_page must be greater than 0",
        )

    return (
        db.query(Customer)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )


@app.get(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    dependencies=[Depends(verify_api_key)],
)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer


@app.put(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    dependencies=[Depends(verify_api_key)],
)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    update_data = customer_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing_customer = (
            db.query(Customer)
            .filter(
                Customer.email == update_data["email"],
                Customer.id != customer_id,
            )
            .first()
        )

        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    for key, value in update_data.items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)
    return customer


@app.delete(
    "/customers/{customer_id}",
    dependencies=[Depends(verify_api_key)],
)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    db.delete(customer)
    db.commit()
    return {"message": "Customer deleted successfully"}
