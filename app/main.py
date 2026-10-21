from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from app.database import engine, Base, SessionLocal
from app.models import Product
from app.config import DEFAULT_CSV_PATH, BASE_DIR
from app.parser import ingest_csv_data
from app.routers.ingestion import router as ingestion_router, sync_data_to_db
from app.routers.analytics import router as analytics_router
from app.routers.inventory import router as inventory_router
from app.routers.forecasting import router as forecasting_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create tables if they do not exist
    Base.metadata.create_all(bind=engine)

    # 2. Check if DB is empty; if so, auto-seed with default knowledge CSV
    db = SessionLocal()
    try:
        count = db.query(Product).count()
        if count == 0 and DEFAULT_CSV_PATH.exists():
            print(f"[*] Initial database empty. Auto-ingesting {DEFAULT_CSV_PATH.name}...")
            data = ingest_csv_data(DEFAULT_CSV_PATH)
            sync_data_to_db(db, data)
            print(f"[+] Ingested {data['products_count']} products and {data['transactions_count']} transactions successfully.")
    except Exception as e:
        print(f"[!] Auto-seeding warning: {e}")
    finally:
        db.close()

    yield

app = FastAPI(
    title="Inventory Turnover & Velocity Engine",
    description="Automated inventory turnover, days sales of inventory (DSI), and velocity analytics.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(ingestion_router)
app.include_router(analytics_router)
app.include_router(inventory_router)
app.include_router(forecasting_router)

# Mount Frontend Static Files
STATIC_DIR = BASE_DIR / "app" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
