import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db, Base, engine
from app.models import Product, Transaction
from app.parser import ingest_csv_data
from app.config import DEFAULT_CSV_PATH, DEFAULT_BASE_YEAR
from app.schemas import IngestionResult

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

def sync_data_to_db(db: Session, data: dict) -> IngestionResult:
    # Clear existing data for a clean sync
    db.query(Transaction).delete()
    db.query(Product).delete()
    db.commit()

    products_data = data["products"]
    for p_info in products_data:
        prod = Product(
            category=p_info["category"],
            sub_category=p_info["sub_category"],
            tool_type=p_info["tool_type"],
            sub_type=p_info["sub_type"],
            product_name=p_info["product_name"],
            unit_cost=p_info["unit_cost"],
            current_stock=p_info["current_stock"],
            total_value=p_info["total_value"],
            supplier_name=p_info["supplier_name"],
        )
        db.add(prod)
        db.flush()  # to obtain prod.id

        for tx in p_info["transactions"]:
            t_obj = Transaction(
                product_id=prod.id,
                transaction_date=tx["transaction_date"],
                transaction_type=tx["transaction_type"],
                quantity=tx["quantity"],
                unit=tx["unit"],
                unit_cost=tx["unit_cost"],
                supplier_name=tx.get("supplier_name", prod.supplier_name),
                raw_text=tx["raw_text"],
            )
            db.add(t_obj)

    db.commit()

    return IngestionResult(
        success=True,
        message="Data successfully parsed and synchronized to database.",
        rows_processed=data["rows_processed"],
        products_created_or_updated=data["products_count"],
        transactions_recorded=data["transactions_count"],
        min_date=data["min_date"],
        max_date=data["max_date"]
    )

@router.post("/default-csv", response_model=IngestionResult)
def ingest_default_csv(base_year: int = DEFAULT_BASE_YEAR, db: Session = Depends(get_db)):
    """
    Ingests the default knowledge CSV file into the database using automated parsing rules.
    """
    if not DEFAULT_CSV_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Default CSV file not found at {DEFAULT_CSV_PATH}")

    try:
        data = ingest_csv_data(DEFAULT_CSV_PATH, base_year=base_year)
        result = sync_data_to_db(db, data)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/upload", response_model=IngestionResult)
async def upload_csv(
    file: UploadFile = File(...),
    base_year: int = DEFAULT_BASE_YEAR,
    db: Session = Depends(get_db)
):
    """
    Upload a new CSV file to replace/update inventory data.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    temp_path = Path("temp_uploaded_inventory.csv")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        data = ingest_csv_data(temp_path, base_year=base_year)
        result = sync_data_to_db(db, data)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload ingestion failed: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()

@router.get("/status")
def get_ingestion_status(db: Session = Depends(get_db)):
    product_count = db.query(Product).count()
    tx_count = db.query(Transaction).count()
    first_tx = db.query(Transaction).order_by(Transaction.transaction_date.asc()).first()
    last_tx = db.query(Transaction).order_by(Transaction.transaction_date.desc()).first()

    return {
        "products_count": product_count,
        "transactions_count": tx_count,
        "earliest_date": str(first_tx.transaction_date) if first_tx else None,
        "latest_date": str(last_tx.transaction_date) if last_tx else None,
        "default_file_exists": DEFAULT_CSV_PATH.exists()
    }
