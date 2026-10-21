from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List
from app.database import get_db
from app.config import DEFAULT_AS_OF_DATE
from app.services.inventory import (
    get_paginated_products,
    get_product_details_with_ledger,
    get_all_categories,
    get_all_suppliers
)
from app.routers.analytics import parse_as_of_date

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

@router.get("/products")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    velocity: Optional[str] = Query(None),
    horizon: str = Query("1m"),
    sort_by: str = Query("cogs"),
    sort_order: str = Query("desc"),
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_paginated_products(
        db=db,
        as_of=as_of_d,
        horizon_key=horizon,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        supplier=supplier,
        velocity_tier=velocity,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/products/{product_id}")
def product_details(product_id: int, db: Session = Depends(get_db)):
    details = get_product_details_with_ledger(db, product_id)
    if not details:
        raise HTTPException(status_code=404, detail="Product not found.")
    return details

@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    return get_all_categories(db)

@router.get("/suppliers", response_model=List[str])
def list_suppliers(db: Session = Depends(get_db)):
    return get_all_suppliers(db)
