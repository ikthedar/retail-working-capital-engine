from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models import Product
from app.routers.analytics import parse_as_of_date
from app.services.forecasting import (
    get_executive_ai_insights,
    compute_product_forecast,
    clear_forecast_cache
)

router = APIRouter(prefix="/api/forecast", tags=["AI Forecasting & Insights"])

@router.get("/insights")
def executive_insights(
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    return get_executive_ai_insights(db, as_of_d)

@router.get("/product-list")
def product_list(
    db: Session = Depends(get_db)
):
    products = db.query(Product.id, Product.product_name, Product.category).filter(
        Product.product_name != "", 
        Product.product_name.isnot(None)
    ).order_by(Product.product_name).all()
    return [{"id": p[0], "product_name": p[1], "category": p[2]} for p in products]

@router.get("/product/{product_id}")
def product_forecast(
    product_id: int,
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return compute_product_forecast(product, as_of_d)

@router.get("/stockout-risks")
def stockout_risks(
    as_of: Optional[str] = Query(None),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    insights = get_executive_ai_insights(db, as_of_d)
    return insights["pillar1_stockout_alerts"]["items"][:limit]

@router.get("/purchase-orders")
def purchase_orders(
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    insights = get_executive_ai_insights(db, as_of_d)
    return insights["pillar2_purchase_orders"]

@router.post("/retrain")
def retrain_models(
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    as_of_d = parse_as_of_date(as_of)
    clear_forecast_cache()
    # Compute and re-populate cache
    insights = get_executive_ai_insights(db, as_of_d)
    return {
        "success": True,
        "message": "AI Forecasting & Pattern models retrained successfully.",
        "insights_summary": {
            "urgent_stockouts": insights["pillar1_stockout_alerts"]["count"],
            "purchase_order_budget": insights["pillar2_purchase_orders"]["total_budget"],
            "surging_skus": insights["pillar3_surging_momentum"]["count"],
            "dead_stock_skus": insights["pillar4_trapped_capital"]["count"]
        }
    }
