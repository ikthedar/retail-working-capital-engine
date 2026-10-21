from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from datetime import date
from app.models import Product, Transaction
from app.services.calculation import compute_product_metrics, get_horizon_dates

def get_paginated_products(
    db: Session,
    as_of: date,
    horizon_key: str = "1m",
    page: int = 1,
    page_size: int = 25,
    search: Optional[str] = None,
    category: Optional[str] = None,
    supplier: Optional[str] = None,
    velocity_tier: Optional[str] = None,
    sort_by: str = "cogs",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    start_date, end_date, days = get_horizon_dates(as_of, horizon_key)
    query = db.query(Product)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.product_name.ilike(term),
                Product.category.ilike(term),
                Product.sub_category.ilike(term),
                Product.tool_type.ilike(term),
                Product.sub_type.ilike(term),
                Product.supplier_name.ilike(term)
            )
        )

    if category and category != "All":
        query = query.filter(Product.category == category)

    if supplier and supplier != "All":
        query = query.filter(Product.supplier_name == supplier)

    products = query.all()

    # Compute metrics for each
    metrics_list = [compute_product_metrics(p, start_date, end_date, days) for p in products]

    if velocity_tier and velocity_tier != "All":
        metrics_list = [m for m in metrics_list if m["velocity_tier"] == velocity_tier.lower()]

    # Sort
    reverse = (sort_order.lower() == "desc")
    if sort_by in ["units_sold", "cogs", "turnover_ratio", "current_stock", "total_value", "unit_cost"]:
        metrics_list.sort(key=lambda x: x.get(sort_by) or 0.0, reverse=reverse)
    elif sort_by == "dsi":
        metrics_list.sort(key=lambda x: (x.get("dsi") is None, x.get("dsi") or 0.0), reverse=reverse)
    else:
        metrics_list.sort(key=lambda x: x.get("product_name", ""), reverse=reverse)

    total_records = len(metrics_list)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = metrics_list[start_idx:end_idx]

    return {
        "items": page_items,
        "total": total_records,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_records + page_size - 1) // page_size if page_size > 0 else 1
    }

def get_product_details_with_ledger(db: Session, product_id: int) -> Optional[Dict[str, Any]]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    txs = sorted(product.transactions, key=lambda t: t.transaction_date, reverse=True)
    tx_list = [
        {
            "id": t.id,
            "date": str(t.transaction_date),
            "type": t.transaction_type,
            "quantity": t.quantity,
            "unit": t.unit,
            "unit_cost": t.unit_cost,
            "total_value": round(t.quantity * t.unit_cost, 2),
            "raw_text": t.raw_text
        }
        for t in txs
    ]

    return {
        "id": product.id,
        "product_name": product.product_name,
        "category": product.category,
        "sub_category": product.sub_category,
        "tool_type": product.tool_type,
        "sub_type": product.sub_type,
        "unit_cost": product.unit_cost,
        "current_stock": product.current_stock,
        "total_value": product.total_value,
        "supplier_name": product.supplier_name,
        "transactions_count": len(tx_list),
        "transactions": tx_list
    }

def get_all_categories(db: Session) -> List[str]:
    results = db.query(Product.category).distinct().order_by(Product.category).all()
    return [r[0] for r in results if r[0]]

def get_all_suppliers(db: Session) -> List[str]:
    results = db.query(Product.supplier_name).distinct().order_by(Product.supplier_name).all()
    return [r[0] for r in results if r[0]]
