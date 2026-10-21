from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models import Product, Transaction
from app.config import HORIZONS, VELOCITY_THRESHOLDS, DEFAULT_AS_OF_DATE

def get_horizon_dates(as_of: date, horizon_key: str):
    if horizon_key not in HORIZONS:
        horizon_key = "1m"
    horizon_info = HORIZONS[horizon_key]
    days = horizon_info["days"]
    if days is None:
        start_date = date(2000, 1, 1)
    else:
        start_date = as_of - timedelta(days=days)
    return start_date, as_of, days

def compute_product_metrics(product: Product, start_date: date, end_date: date, days: Optional[int]) -> Dict[str, Any]:
    txs = product.transactions

    # Filter transactions within window
    window_sales = [t for t in txs if t.transaction_type == "SALE" and start_date <= t.transaction_date <= end_date]
    units_sold = sum(t.quantity for t in window_sales)
    cogs = units_sold * product.unit_cost

    # Reconstruct Beginning Inventory
    # Stock at start = Current Stock + (Sales from start to present) - (Purchases from start to present)
    future_sales = sum(t.quantity for t in txs if t.transaction_type == "SALE" and t.transaction_date >= start_date)
    future_purchases = sum(t.quantity for t in txs if t.transaction_type == "PURCHASE" and t.transaction_date >= start_date)
    
    reconstructed_start_stock = max(0.0, product.current_stock + future_sales - future_purchases)
    ending_stock = product.current_stock

    avg_stock = (reconstructed_start_stock + ending_stock) / 2.0
    if avg_stock <= 0:
        avg_stock = product.current_stock

    avg_inventory_val = avg_stock * product.unit_cost
    if avg_inventory_val <= 0:
        avg_inventory_val = product.total_value

    # Turnover Ratio
    if avg_inventory_val > 0 and cogs > 0:
        turnover_ratio = cogs / avg_inventory_val
    else:
        turnover_ratio = 0.0

    # Annualized Turnover
    effective_days = days if days else 365
    annualized_turnover = turnover_ratio * (365.0 / effective_days) if effective_days > 0 else turnover_ratio

    # Days Sales of Inventory (DSI)
    if cogs > 0 and avg_inventory_val > 0:
        dsi = (avg_inventory_val / cogs) * effective_days
    else:
        dsi = None

    # Run-out days (Stock Cover)
    if units_sold > 0 and effective_days > 0:
        daily_rate = units_sold / effective_days
        run_out_days = product.current_stock / daily_rate if daily_rate > 0 else None
    else:
        run_out_days = None

    # Velocity Tier
    if units_sold == 0 or cogs == 0:
        velocity_tier = "dead"
    elif dsi is not None and dsi <= VELOCITY_THRESHOLDS["fast"]:
        velocity_tier = "fast"
    elif dsi is not None and dsi <= VELOCITY_THRESHOLDS["medium"]:
        velocity_tier = "medium"
    elif dsi is not None and dsi <= VELOCITY_THRESHOLDS["slow"]:
        velocity_tier = "slow"
    else:
        velocity_tier = "dead"

    return {
        "id": product.id,
        "product_name": product.product_name,
        "category": product.category,
        "sub_category": product.sub_category,
        "tool_type": product.tool_type,
        "sub_type": product.sub_type,
        "supplier_name": product.supplier_name,
        "unit_cost": product.unit_cost,
        "current_stock": product.current_stock,
        "total_value": product.total_value,
        "units_sold": round(units_sold, 2),
        "cogs": round(cogs, 2),
        "avg_inventory_value": round(avg_inventory_val, 2),
        "turnover_ratio": round(turnover_ratio, 4),
        "annualized_turnover": round(annualized_turnover, 2),
        "dsi": round(dsi, 1) if dsi is not None else None,
        "run_out_days": round(run_out_days, 1) if run_out_days is not None else None,
        "velocity_tier": velocity_tier
    }

def get_kpi_summary(db: Session, as_of: date, horizon_key: str) -> Dict[str, Any]:
    start_date, end_date, days = get_horizon_dates(as_of, horizon_key)
    products = db.query(Product).all()

    total_value = sum(p.total_value for p in products)
    total_stock = sum(p.current_stock for p in products)
    total_products_count = len(products)

    period_cogs = 0.0
    period_units = 0.0
    active_count = 0
    total_avg_inventory = 0.0
    dsi_sum = 0.0
    dsi_count = 0

    for p in products:
        m = compute_product_metrics(p, start_date, end_date, days)
        period_cogs += m["cogs"]
        period_units += m["units_sold"]
        total_avg_inventory += m["avg_inventory_value"]
        if m["units_sold"] > 0:
            active_count += 1
        if m["dsi"] is not None:
            dsi_sum += m["dsi"]
            dsi_count += 1

    overall_turnover = period_cogs / total_avg_inventory if total_avg_inventory > 0 else 0.0
    effective_days = days if days else 365
    annualized_turnover = overall_turnover * (365.0 / effective_days) if effective_days > 0 else overall_turnover
    avg_dsi = dsi_sum / dsi_count if dsi_count > 0 else None

    return {
        "as_of_date": str(as_of),
        "horizon_key": horizon_key,
        "horizon_days": days,
        "total_inventory_value": round(total_value, 2),
        "total_stock_units": round(total_stock, 2),
        "total_products_count": total_products_count,
        "active_moving_products_count": active_count,
        "period_cogs": round(period_cogs, 2),
        "period_units_sold": round(period_units, 2),
        "overall_turnover_ratio": round(overall_turnover, 4),
        "overall_annualized_turnover": round(annualized_turnover, 2),
        "average_dsi": round(avg_dsi, 1) if avg_dsi is not None else None
    }

def get_top_products(
    db: Session,
    as_of: date,
    horizon_key: str,
    sort_by: str = "units",
    limit: int = 10,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    start_date, end_date, days = get_horizon_dates(as_of, horizon_key)
    query = db.query(Product)
    if category and category != "All":
        query = query.filter(Product.category == category)
    products = query.all()

    metrics_list = [compute_product_metrics(p, start_date, end_date, days) for p in products]

    if sort_by == "cogs":
        sorted_list = sorted(metrics_list, key=lambda x: (x["cogs"], x["units_sold"]), reverse=True)
    else:
        sorted_list = sorted(metrics_list, key=lambda x: (x["units_sold"], x["cogs"]), reverse=True)

    result = []
    for rank, item in enumerate(sorted_list[:limit], start=1):
        item["rank"] = rank
        result.append(item)
    return result

def get_top_suppliers(
    db: Session,
    as_of: date,
    horizon_key: str,
    sort_by: str = "units",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Ranks suppliers based on products sold in the specified time horizon.
    Uses transaction-level supplier lineage for accurate historical attribution.
    """
    start_date, end_date, days = get_horizon_dates(as_of, horizon_key)
    products = db.query(Product).all()

    supplier_map: Dict[str, Dict[str, Any]] = {}
    effective_days = days if days else 365

    # 1. Attribute active inventory & catalog SKUs to each product's active supplier
    for p in products:
        s_name = p.supplier_name or "Unknown"
        if s_name not in supplier_map:
            supplier_map[s_name] = {
                "supplier_name": s_name,
                "sku_count": 0,
                "current_stock": 0.0,
                "total_inventory_value": 0.0,
                "units_sold": 0.0,
                "cogs": 0.0,
                "avg_inventory_value": 0.0,
                "dsi_sum": 0.0,
                "dsi_count": 0
            }

        sm = supplier_map[s_name]
        sm["sku_count"] += 1
        sm["current_stock"] += p.current_stock
        sm["total_inventory_value"] += p.total_value

    # 2. Attribute sales & COGS in the horizon by Transaction.supplier_name
    sales_txs = (
        db.query(Transaction)
        .filter(
            Transaction.transaction_type == "SALE",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )
        .all()
    )

    for tx in sales_txs:
        tx_sup = tx.supplier_name if (tx.supplier_name and tx.supplier_name != "Unknown") else (tx.product.supplier_name if tx.product else "Unknown")
        if tx_sup not in supplier_map:
            supplier_map[tx_sup] = {
                "supplier_name": tx_sup,
                "sku_count": 0,
                "current_stock": 0.0,
                "total_inventory_value": 0.0,
                "units_sold": 0.0,
                "cogs": 0.0,
                "avg_inventory_value": 0.0,
                "dsi_sum": 0.0,
                "dsi_count": 0
            }
        sm = supplier_map[tx_sup]
        sm["units_sold"] += tx.quantity
        cost = tx.unit_cost or (tx.product.unit_cost if tx.product else 0.0)
        sm["cogs"] += tx.quantity * cost

    suppliers_list = list(supplier_map.values())
    for s in suppliers_list:
        s["avg_inventory_value"] = s["total_inventory_value"]
        s["turnover_ratio"] = round(s["cogs"] / s["avg_inventory_value"], 4) if s["avg_inventory_value"] > 0 else 0.0
        if s["cogs"] > 0 and s["avg_inventory_value"] > 0:
            s["average_dsi"] = round((s["avg_inventory_value"] / s["cogs"]) * effective_days, 1)
        else:
            s["average_dsi"] = None

        s["total_inventory_value"] = round(s["total_inventory_value"], 2)
        s["current_stock"] = round(s["current_stock"], 2)
        s["units_sold"] = round(s["units_sold"], 2)
        s["cogs"] = round(s["cogs"], 2)

    if sort_by == "cogs":
        sorted_suppliers = sorted(suppliers_list, key=lambda x: (x["cogs"], x["units_sold"]), reverse=True)
    else:
        sorted_suppliers = sorted(suppliers_list, key=lambda x: (x["units_sold"], x["cogs"]), reverse=True)

    result = []
    for rank, s in enumerate(sorted_suppliers[:limit], start=1):
        s["rank"] = rank
        result.append(s)
    return result

def get_supplier_detail(
    db: Session,
    supplier_name: str,
    as_of: date,
    horizon_key: str
) -> Dict[str, Any]:
    """
    Computes granular performance, sold products (turnover drivers),
    and complete active inventory valuation for a specific supplier
    using transaction-level supplier lineage.
    """
    start_date, end_date, days = get_horizon_dates(as_of, horizon_key)
    effective_days = days if days else 365

    # 1. Active inventory SKUs for this supplier
    active_inventory_q = db.query(Product).filter(Product.supplier_name == supplier_name).all()

    sku_count = len(active_inventory_q)
    total_inventory_value = sum(p.total_value for p in active_inventory_q)
    current_stock = sum(p.current_stock for p in active_inventory_q)

    # 2. Sales in the window specifically tagged with this supplier_name
    sales_txs = (
        db.query(Transaction)
        .join(Product)
        .filter(
            Transaction.transaction_type == "SALE",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            (
                (Transaction.supplier_name == supplier_name) |
                ((Transaction.supplier_name.is_(None) | (Transaction.supplier_name == "Unknown")) & (Product.supplier_name == supplier_name))
            )
        )
        .all()
    )

    prod_sales_map = {}
    total_units_sold = 0.0
    total_cogs = 0.0

    for tx in sales_txs:
        pid = tx.product_id
        if pid not in prod_sales_map:
            prod_sales_map[pid] = {
                "product": tx.product,
                "units_sold": 0.0,
                "cogs": 0.0
            }
        prod_sales_map[pid]["units_sold"] += tx.quantity
        cost = tx.unit_cost or (tx.product.unit_cost if tx.product else 0.0)
        prod_sales_map[pid]["cogs"] += tx.quantity * cost
        total_units_sold += tx.quantity
        total_cogs += tx.quantity * cost

    sold_products = []
    for pid, pdata in prod_sales_map.items():
        p = pdata["product"]
        u_sold = pdata["units_sold"]
        cogs_val = pdata["cogs"]
        t_ratio = round(cogs_val / p.total_value, 4) if p.total_value > 0 else 0.0
        dsi_val = round((p.total_value / cogs_val) * effective_days, 1) if (cogs_val > 0 and p.total_value > 0) else None

        if u_sold == 0:
            v_tier = "dead"
        elif dsi_val is not None and dsi_val <= 45:
            v_tier = "fast"
        elif dsi_val is not None and dsi_val <= 90:
            v_tier = "medium"
        elif dsi_val is not None and dsi_val <= 180:
            v_tier = "slow"
        else:
            v_tier = "dead"

        sold_products.append({
            "id": p.id,
            "product_name": p.product_name,
            "category": p.category,
            "sub_category": p.sub_category,
            "unit_cost": round(p.unit_cost, 2),
            "current_stock": round(p.current_stock, 2),
            "total_value": round(p.total_value, 2),
            "units_sold": round(u_sold, 2),
            "cogs": round(cogs_val, 2),
            "turnover_ratio": t_ratio,
            "dsi": dsi_val,
            "velocity_tier": v_tier
        })

    for sp in sold_products:
        sp["turnover_impact_pct"] = round((sp["cogs"] / total_cogs) * 100.0, 1) if total_cogs > 0 else 0.0
    sold_products.sort(key=lambda x: (x["cogs"], x["units_sold"]), reverse=True)

    # Complete active inventory products
    inventory_products = []
    for p in active_inventory_q:
        s_info = prod_sales_map.get(p.id)
        u_sold = s_info["units_sold"] if s_info else 0.0
        inventory_products.append({
            "id": p.id,
            "product_name": p.product_name,
            "category": p.category,
            "sub_category": p.sub_category,
            "unit_cost": round(p.unit_cost, 2),
            "current_stock": round(p.current_stock, 2),
            "total_value": round(p.total_value, 2),
            "units_sold": round(u_sold, 2),
            "velocity_tier": "fast" if u_sold > 0 else "dead"
        })
    inventory_products.sort(key=lambda x: (x["total_value"], x["current_stock"]), reverse=True)

    turnover_ratio = round(total_cogs / total_inventory_value, 4) if total_inventory_value > 0 else 0.0
    avg_dsi = round((total_inventory_value / total_cogs) * effective_days, 1) if (total_cogs > 0 and total_inventory_value > 0) else None

    return {
        "summary": {
            "supplier_name": supplier_name,
            "sku_count": sku_count,
            "total_inventory_value": round(total_inventory_value, 2),
            "current_stock": round(current_stock, 2),
            "units_sold": round(total_units_sold, 2),
            "cogs": round(total_cogs, 2),
            "turnover_ratio": turnover_ratio,
            "average_dsi": avg_dsi,
            "horizon": horizon_key
        },
        "sold_products": sold_products,
        "inventory_products": inventory_products
    }

def get_velocity_distribution(db: Session, as_of: date, horizon_key: str) -> Dict[str, Any]:
    start_date, end_date, days = get_horizon_dates(as_of, horizon_key)
    products = db.query(Product).all()

    tiers = {
        "fast": {"count": 0, "inventory_value": 0.0},
        "medium": {"count": 0, "inventory_value": 0.0},
        "slow": {"count": 0, "inventory_value": 0.0},
        "dead": {"count": 0, "inventory_value": 0.0},
    }

    total_skus = len(products)
    total_val = sum(p.total_value for p in products) or 1.0

    for p in products:
        m = compute_product_metrics(p, start_date, end_date, days)
        t = m["velocity_tier"]
        tiers[t]["count"] += 1
        tiers[t]["inventory_value"] += p.total_value

    response = {}
    for tier_key, data in tiers.items():
        response[tier_key] = {
            "count": data["count"],
            "inventory_value": round(data["inventory_value"], 2),
            "percentage_skus": round((data["count"] / total_skus) * 100, 1) if total_skus > 0 else 0.0,
            "percentage_value": round((data["inventory_value"] / total_val) * 100, 1)
        }
    return response

def get_category_performance(db: Session, as_of: date, horizon_key: str) -> List[Dict[str, Any]]:
    start_date, end_date, days = get_horizon_dates(as_of, horizon_key)
    products = db.query(Product).all()

    cat_map: Dict[str, Dict[str, Any]] = {}
    for p in products:
        c_name = p.category or "Uncategorized"
        if c_name not in cat_map:
            cat_map[c_name] = {
                "category": c_name,
                "sku_count": 0,
                "current_stock": 0.0,
                "total_inventory_value": 0.0,
                "units_sold": 0.0,
                "cogs": 0.0,
                "avg_inventory_value": 0.0,
                "dsi_sum": 0.0,
                "dsi_count": 0
            }

        m = compute_product_metrics(p, start_date, end_date, days)
        cm = cat_map[c_name]
        cm["sku_count"] += 1
        cm["current_stock"] += p.current_stock
        cm["total_inventory_value"] += p.total_value
        cm["units_sold"] += m["units_sold"]
        cm["cogs"] += m["cogs"]
        cm["avg_inventory_value"] += m["avg_inventory_value"]
        if m["dsi"] is not None:
            cm["dsi_sum"] += m["dsi"]
            cm["dsi_count"] += 1

    result = []
    for c in cat_map.values():
        c["turnover_ratio"] = round(c["cogs"] / c["avg_inventory_value"], 4) if c["avg_inventory_value"] > 0 else 0.0
        c["average_dsi"] = round(c["dsi_sum"] / c["dsi_count"], 1) if c["dsi_count"] > 0 else None
        c["total_inventory_value"] = round(c["total_inventory_value"], 2)
        c["current_stock"] = round(c["current_stock"], 2)
        c["units_sold"] = round(c["units_sold"], 2)
        c["cogs"] = round(c["cogs"], 2)
        result.append(c)

    result.sort(key=lambda x: x["cogs"], reverse=True)
    return result
