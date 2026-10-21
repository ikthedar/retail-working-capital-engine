# ⚡ Retail Inventory Turnover Velocity & Supplier Intelligence Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

> A high-performance quantitative inventory analytics platform and machine learning forecasting engine. Reconciles transaction-level multi-supplier batch lineage, calculates vectorized Days Sales of Inventory (DSI) and inventory turnover ratios across multi-horizon timeframes, and detects dormant capital tie-up.

---

## 🎯 The Problem

In high-volume retail and distribution businesses, inventory is both an asset and a balance-sheet vulnerability:
1. **Dead Capital Lock-up**: Capital tied up in stagnant SKUs reduces working liquidity, leading to high holding costs and inventory write-offs.
2. **Multi-Supplier Batch Confusion**: SKUs are frequently purchased from different suppliers across different seasons. Legacy ERPs overwrite the supplier attribute, falsely assigning older sales/COGS to the current vendor or vice versa.
3. **Static Reorder Blind Spots**: Traditional periodic reordering fails to adapt to recent velocity shifts, leading to unexpected stockouts on fast movers and over-purchasing on declining items.

---

## 🚀 Key Architecture & Capabilities

┌─────────────────────────┐ │ Multi-Vendor CSV/ERP │ │ Transaction Logs (7.4k+)│ └────────────┬────────────┘ │ Ingestion & Lineage Parser ▼ ┌────────────────────────────────────────────────────────┐ │ Intelligent 3-Tier Lineage Engine │ │ • Transaction.supplier_name: Exact batch provenance │ │ • Product.supplier_name: Stock > 0 & recency hierarchy │ └────────────┬───────────────────────────────────────────┘ │ ├──► [ Vectorized Financial Turnover & DSI Engine ] │ ├── Dynamic Horizons: 7d, 14d, 30d, 90d, 180d, 365d, All-Time │ ├── Velocity Classification: Fast, Medium, Slow, Dead │ └── Supplier Leaderboard & SKU COGS Impact Attribution │ └──► [ AI / ML Demand & Replenishment Forecaster ] ├── Next-Period Demand Projection ├── Safety Stock & Reorder Point (ROP) Modeling └── Stockout Depletion Run-Rate Horizons


### 1. Transaction-Level Supplier Lineage Reconciler
* Solves multi-vendor SKU drift by binding every individual purchase and sale transaction to its historical supplier (`Transaction.supplier_name`).
* Dynamically resolves active product ownership (`Product.supplier_name`) using a 3-tier hierarchy:
  1. Vendor holding positive physical stock (`stock > 0`).
  2. Vendor with the most recent transaction timestamp.
  3. Last documented batch provenance.

### 2. Multi-Horizon Financial Velocity Engine
* Evaluates Cost of Goods Sold (COGS), Average Inventory Valuation, and Turnover Ratio across flexible evaluation windows (**7 Days, 14 Days, 30 Days, 90 Days, 180 Days, 365 Days, All-Time Inception**).
* Calculates exact **Days Sales of Inventory (DSI)**:
  $$\text{Turnover Ratio} = \frac{\text{COGS}_{\text{window}}}{\text{Current Inventory Value}}$$
  $$\text{DSI} = \left(\frac{\text{Current Inventory Value}}{\text{COGS}_{\text{window}}}\right) \times \text{Window Days}$$

### 3. Automated Capital Velocity Tiers
Automatically segments every product in the catalog to pinpoint balance-sheet bottlenecks:
* **FAST ($\le 45$ days)**: High liquidity drivers; prioritize vendor supply continuity.
* **MEDIUM (46–90 days)**: Healthy operational rotation.
* **SLOW (91–180 days)**: At risk of stagnation; monitor reorder volume.
* **DEAD ($> 180$ days or 0 sales)**: Frozen capital; immediate candidate for liquidation/discounting.

### 4. Interactive Supplier Intelligence Drill-Down
* Real-time inspection drawer for any wholesale vendor:
  * **Turnover Impact**: Breaks down which specific SKUs generate what percentage share of that vendor's total COGS.
  * **Complete Active Inventory**: Inspects all active stock units, unit costs, and total valuation currently held from that supplier.

### 5. ML Demand Forecasting & Replenishment Intelligence
* Forecasts upcoming demand velocity using rolling variance, trend adjustments, and seasonality.
* Computes dynamic **Safety Stock** and **Reorder Points (ROP)**:
  $$\text{Safety Stock} = Z \times \sigma_d \times \sqrt{L}$$
  $$\text{Reorder Point (ROP)} = (d \times L) + \text{Safety Stock}$$
* Accurately flags items nearing their stockout exhaustion horizon.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.10+, FastAPI (Async REST API), SQLAlchemy 2.0 ORM, Pydantic v2
* **Storage**: SQLite / PostgreSQL (acid-compliant transactional ledger)
* **Data Science / ML**: Pandas, NumPy, Scikit-learn
* **Frontend**: Vanilla CSS (Custom Design System, Responsive Glassmorphism, Dark Mode Palette), Modern ES6 JavaScript, Chart.js
* **Tooling**: Uvicorn, Python Virtual Environment (`.venv`)

---

## ⚡ Quickstart

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/inventory-turnover-velocity.git
cd inventory-turnover-velocity

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt


### 2. Ingest Data & Initialize Ledger
bash
python -c "from app.database import init_db; from app.routers.ingestion import sync_data_to_db; from app.database import SessionLocal; init_db(); sync_data_to_db(SessionLocal())"

### 3. Launch Local Server
bash
python run.py
Visit http://127.0.0.1:8000 in your browser to access the dashboard.

📡 REST API Reference
Endpoint	Method	Description
/api/analytics/kpi-summary	GET	Catalog-wide inventory value, periodic COGS, turnover, and average DSI
/api/analytics/top-products	GET	Top selling SKUs by units or COGS value with velocity tier badges
/api/analytics/top-suppliers	GET	Supplier leaderboard ranked by sales volume, COGS, and turnover
/api/analytics/supplier-detail	GET	Deep-dive modal payload: SKU turnover impact % and active inventory breakdown
/api/analytics/velocity-distribution	GET	Distribution breakdown across Fast, Medium, Slow, and Dead capital
/api/forecasting/predict	GET	ML-driven demand projections, safety stock, and reorder alerts
