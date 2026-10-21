import re
import csv
from datetime import date
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from app.config import DEFAULT_BASE_YEAR, DEFAULT_CSV_PATH

MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

def clean_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    s = str(val).strip().replace(",", "").replace("$", "").replace("৳", "")
    if not s or s == "-" or s == "??" or s == "nan":
        return default
    try:
        return float(s)
    except ValueError:
        return default

def clean_str(val: Any, default: str = "") -> str:
    if val is None:
        return default
    s = str(val).strip()
    return default if s in ["??", "nan", "-"] else s

def parse_transaction_chunk(
    chunk: str,
    active_year: int,
    default_type: str = "SALE"
) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Parses a single semicolon-delimited transaction phrase.
    Returns (transaction_dict, updated_active_year).
    """
    text = chunk.strip()
    if not text:
        return None, active_year

    # Check for explicit year (e.g. 2025, 2026, 2027)
    year_match = re.search(r'\b(202\d)\b', text)
    if year_match:
        active_year = int(year_match.group(1))

    # Detect transaction type
    lower_text = text.lower()
    if "not found" in lower_text or "shrink" in lower_text or "loss" in lower_text or "damage" in lower_text:
        tx_type = "SHRINKAGE"
    elif "bought" in lower_text or "brought" in lower_text or default_type == "PURCHASE":
        tx_type = "PURCHASE"
    else:
        tx_type = "SALE"

    # Extract Quantity and Unit
    # Patterns: "2pc", "2 pcs", "20ft", "1set", "2"
    qty = 0.0
    unit = "pc"
    qty_match = re.search(r'(\d+(?:\.\d+)?)\s*(pc|pcs|ft|feet|set|sets)?', lower_text)
    if qty_match:
        try:
            qty = float(qty_match.group(1))
            if qty_match.group(2):
                unit = qty_match.group(2)
                if unit in ["pcs", "pc"]:
                    unit = "pc"
                elif unit in ["feet", "ft"]:
                    unit = "ft"
                elif unit in ["sets", "set"]:
                    unit = "set"
        except ValueError:
            return None, active_year
    else:
        return None, active_year

    if qty <= 0:
        return None, active_year

    # Extract Date: Month and Day
    # Matches: "May 6", "Feb 2", "Apr 8th", "Jan 28", "06/05", "May 6, 2026"
    month = None
    day = None

    # First check month names
    for m_str, m_num in MONTH_MAP.items():
        m_regex = rf'\b{m_str}\b\.?\s*(\d{{1,2}})(?:st|nd|rd|th)?'
        m_match = re.search(m_regex, lower_text)
        if m_match:
            month = m_num
            day = int(m_match.group(1))
            break
        # Reverse check: "8th Apr" or "8 Apr"
        m_rev_regex = rf'(\d{{1,2}})(?:st|nd|rd|th)?\s*\b{m_str}\b'
        m_rev_match = re.search(m_rev_regex, lower_text)
        if m_rev_match:
            month = m_num
            day = int(m_rev_match.group(1))
            break

    if not month or not day:
        # Check numeric date format: MM/DD or DD/MM
        num_date_match = re.search(r'\b(\d{1,2})[/-](\d{1,2})\b', lower_text)
        if num_date_match:
            d1 = int(num_date_match.group(1))
            d2 = int(num_date_match.group(2))
            if d1 <= 12 and d2 <= 31:
                month, day = d1, d2
            elif d2 <= 12 and d1 <= 31:
                month, day = d2, d1

    if not month or not day:
        # If no date could be parsed, skip
        return None, active_year

    # Clamp day to valid range for month
    try:
        parsed_date = date(active_year, month, min(day, 28 if month == 2 else 30))
    except ValueError:
        parsed_date = date(active_year, month, 1)

    return {
        "transaction_date": parsed_date,
        "transaction_type": tx_type,
        "quantity": qty,
        "unit": unit,
        "raw_text": text
    }, active_year

def parse_transaction_string(raw_str: str, default_type: str = "SALE", base_year: int = DEFAULT_BASE_YEAR) -> List[Dict[str, Any]]:
    if not raw_str or not raw_str.strip():
        return []

    # Delimiters: semicolon, newline
    chunks = re.split(r'[;\n]+', raw_str)
    transactions = []
    current_year = base_year

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        parsed_tx, current_year = parse_transaction_chunk(chunk, current_year, default_type=default_type)
        if parsed_tx:
            transactions.append(parsed_tx)

    return transactions

def ingest_csv_data(filepath: Optional[Path] = None, base_year: int = DEFAULT_BASE_YEAR) -> Dict[str, Any]:
    """
    Parses CSV and consolidates products according to Bucket 1 specification.
    Returns structured dict ready for DB insertion.
    """
    path = filepath or DEFAULT_CSV_PATH
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found at: {path}")

    consolidated_products: Dict[str, Dict[str, Any]] = {}
    rows_processed = 0

    with open(path, mode="r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)

        for row in reader:
            if not row or len(row) < 5:
                continue

            # Check if empty spacer row
            if all(not cell.strip() for cell in row):
                continue

            category = clean_str(row[0] if len(row) > 0 else "")
            sub_category = clean_str(row[1] if len(row) > 1 else "")
            tool_type = clean_str(row[2] if len(row) > 2 else "")
            sub_type = clean_str(row[3] if len(row) > 3 else "")
            product_name = clean_str(row[4] if len(row) > 4 else "")

            if not product_name and not category:
                continue

            unit_cost = clean_float(row[5] if len(row) > 5 else 0.0)
            current_stock = clean_float(row[6] if len(row) > 6 else 0.0)
            supplier_name = clean_str(row[8] if len(row) > 8 else "Unknown")
            if not supplier_name:
                supplier_name = "Unknown"

            items_sold_str = row[9] if len(row) > 9 else ""
            items_bought_str = row[10] if len(row) > 10 else ""

            # Unique key for consolidation
            prod_key = f"{category}|{sub_category}|{tool_type}|{sub_type}|{product_name}".lower()

            sold_txs = parse_transaction_string(items_sold_str, default_type="SALE", base_year=base_year)
            bought_txs = parse_transaction_string(items_bought_str, default_type="PURCHASE", base_year=base_year)
            all_row_txs = sold_txs + bought_txs

            # Approach A: Tag each transaction with its row's actual supplier and cost
            for tx in all_row_txs:
                tx["supplier_name"] = supplier_name
                tx["unit_cost"] = unit_cost if unit_cost > 0 else 0.0

            row_max_date = max((t["transaction_date"] for t in all_row_txs), default=None)
            batch_entry = {
                "supplier_name": supplier_name,
                "stock": current_stock,
                "cost": unit_cost,
                "max_date": row_max_date
            }

            if prod_key not in consolidated_products:
                consolidated_products[prod_key] = {
                    "category": category,
                    "sub_category": sub_category,
                    "tool_type": tool_type,
                    "sub_type": sub_type,
                    "product_name": product_name,
                    "stock_batches": [(current_stock, unit_cost)],
                    "supplier_batches": [batch_entry],
                    "total_stock": current_stock,
                    "transactions": all_row_txs
                }
            else:
                prod = consolidated_products[prod_key]
                prod["stock_batches"].append((current_stock, unit_cost))
                prod["supplier_batches"].append(batch_entry)
                prod["total_stock"] += current_stock
                prod["transactions"].extend(all_row_txs)

            rows_processed += 1

    # Finalize weighted average cost and determine active supplier for each consolidated product
    final_products = []
    min_date = None
    max_date = None
    total_tx_count = 0

    for prod in consolidated_products.values():
        total_stock = prod["total_stock"]
        total_cost_val = sum(s * c for s, c in prod["stock_batches"])
        
        if total_stock > 0 and total_cost_val > 0:
            avg_unit_cost = total_cost_val / total_stock
        else:
            # Fallback to the latest non-zero unit cost
            non_zero_costs = [c for _, c in prod["stock_batches"] if c > 0]
            avg_unit_cost = non_zero_costs[-1] if non_zero_costs else 0.0

        total_value = total_stock * avg_unit_cost

        # Determine Primary/Active Supplier:
        # Priority 1: Supplier holding active physical stock (stock > 0 and supplier != "Unknown")
        stock_batches = [b for b in prod["supplier_batches"] if b["stock"] > 0 and b["supplier_name"] != "Unknown"]
        if stock_batches:
            stock_batches.sort(key=lambda x: (x["stock"], x["max_date"] or date.min), reverse=True)
            active_supplier = stock_batches[0]["supplier_name"]
        else:
            # Priority 2: If physical stock is 0, supplier with the latest transaction activity
            dated_batches = [b for b in prod["supplier_batches"] if b["max_date"] is not None and b["supplier_name"] != "Unknown"]
            if dated_batches:
                dated_batches.sort(key=lambda x: x["max_date"], reverse=True)
                active_supplier = dated_batches[0]["supplier_name"]
            else:
                # Priority 3: Fallback to latest known supplier in row list
                known_batches = [b for b in prod["supplier_batches"] if b["supplier_name"] != "Unknown"]
                active_supplier = known_batches[-1]["supplier_name"] if known_batches else "Unknown"

        # Finalize transactions
        for tx in prod["transactions"]:
            if tx.get("unit_cost", 0.0) <= 0.0:
                tx["unit_cost"] = avg_unit_cost
            if not tx.get("supplier_name") or tx["supplier_name"] == "Unknown":
                tx["supplier_name"] = active_supplier

            tx_d = tx["transaction_date"]
            if min_date is None or tx_d < min_date:
                min_date = tx_d
            if max_date is None or tx_d > max_date:
                max_date = tx_d
            total_tx_count += 1

        final_products.append({
            "category": prod["category"],
            "sub_category": prod["sub_category"],
            "tool_type": prod["tool_type"],
            "sub_type": prod["sub_type"],
            "product_name": prod["product_name"],
            "unit_cost": round(avg_unit_cost, 2),
            "current_stock": round(total_stock, 2),
            "total_value": round(total_value, 2),
            "supplier_name": active_supplier,
            "transactions": prod["transactions"]
        })

    return {
        "products": final_products,
        "rows_processed": rows_processed,
        "products_count": len(final_products),
        "transactions_count": total_tx_count,
        "min_date": str(min_date) if min_date else None,
        "max_date": str(max_date) if max_date else None,
    }
