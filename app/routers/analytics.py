from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional, List
from app.database import get_db
from app.config import DEFAULT_AS_OF_DATE
from app.services.calculation import (
    get_kpi_summary,
    get_top_products,
    get_top_suppliers,
    get_supplier_detail,
    get_velocity_distribution,
    get_category_performance
)
from app.schemas import (
    KPISummary,
    TopProductItem,
    TopSupplierItem,
    VelocityDistributionResponse,
    CategoryPerformanceItem
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

def parse_as_of_date(as_of: Optional[str]) -> date:
    if not as_of or as_of.strip() == "":
        return datetime.strptime(DEFAULT_AS_OF_DATE, "%Y-%m-%d").date()
    try:
        return datetime.strptime(as_of.strip(), "%Y-%m-%d").date()
    except ValueError:
        return datetime.strptime(DEFAULT_AS_OF_DATE, "%Y-%m-%d").date()

@router.get("/kpi-summary", response_model=KPISummary)
def kpi_summary(
    horizon: str = Query("1m", description="1w, 2w, 1m, 3m, 6m, 12m, all"),
    as_of: Optional[str] = Query(None, description="Evaluation As-Of date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_kpi_summary(db, as_of_d, horizon)

@router.get("/top-products", response_model=List[TopProductItem])
def top_products(
    horizon: str = Query("1m", description="1w, 2w, 1m, 3m, 6m, 12m, all"),
    sort_by: str = Query("units", description="units (volume) or cogs (value)"),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_top_products(db, as_of_d, horizon, sort_by=sort_by, limit=limit, category=category)

@router.get("/top-suppliers", response_model=List[TopSupplierItem])
def top_suppliers(
    horizon: str = Query("1m", description="1w, 2w, 1m, 3m, 6m, 12m, all"),
    sort_by: str = Query("units", description="units (volume) or cogs (value)"),
    limit: int = Query(10, ge=1, le=100),
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_top_suppliers(db, as_of_d, horizon, sort_by=sort_by, limit=limit)

@router.get("/supplier-detail")
def supplier_detail(
    supplier_name: str = Query(..., description="Name of the supplier"),
    horizon: str = Query("1m", description="1w, 2w, 1m, 3m, 6m, 12m, all"),
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_supplier_detail(db, supplier_name, as_of_d, horizon)

@router.get("/velocity-distribution", response_model=VelocityDistributionResponse)
def velocity_distribution(
    horizon: str = Query("1m"),
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_velocity_distribution(db, as_of_d, horizon)

@router.get("/category-performance", response_model=List[CategoryPerformanceItem])
def category_performance(
    horizon: str = Query("1m"),
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_category_performance(db, as_of_d, horizon)
