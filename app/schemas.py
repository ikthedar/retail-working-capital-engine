from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class TransactionBase(BaseModel):
    transaction_date: date
    transaction_type: str
    quantity: float
    unit: str
    unit_cost: float
    raw_text: str

class TransactionRead(TransactionBase):
    id: int
    product_id: int
    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    category: str
    sub_category: str
    tool_type: str
    sub_type: str
    product_name: str
    unit_cost: float
    current_stock: float
    total_value: float
    supplier_name: str

class ProductRead(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ProductWithTransactions(ProductRead):
    transactions: List[TransactionRead] = []

class ProductMetrics(BaseModel):
    id: int
    product_name: str
    category: str
    sub_category: str
    tool_type: str
    sub_type: str
    supplier_name: str
    unit_cost: float
    current_stock: float
    total_value: float
    units_sold: float
    cogs: float
    avg_inventory_value: float
    turnover_ratio: float
    annualized_turnover: float
    dsi: Optional[float]
    run_out_days: Optional[float]
    velocity_tier: str  # 'fast', 'medium', 'slow', 'dead'

class KPISummary(BaseModel):
    as_of_date: str
    horizon_key: str
    horizon_days: Optional[int]
    total_inventory_value: float
    total_stock_units: float
    total_products_count: int
    active_moving_products_count: int
    period_cogs: float
    period_units_sold: float
    overall_turnover_ratio: float
    overall_annualized_turnover: float
    average_dsi: Optional[float]

class TopProductItem(BaseModel):
    rank: int
    id: int
    product_name: str
    category: str
    supplier_name: str
    unit_cost: float
    current_stock: float
    total_value: float
    units_sold: float
    cogs: float
    turnover_ratio: float
    dsi: Optional[float]
    run_out_days: Optional[float]
    velocity_tier: str

class TopSupplierItem(BaseModel):
    rank: int
    supplier_name: str
    sku_count: int
    current_stock: float
    total_inventory_value: float
    units_sold: float
    cogs: float
    turnover_ratio: float
    average_dsi: Optional[float]

class VelocityTierCount(BaseModel):
    count: int
    inventory_value: float
    percentage_skus: float
    percentage_value: float

class VelocityDistributionResponse(BaseModel):
    fast: VelocityTierCount
    medium: VelocityTierCount
    slow: VelocityTierCount
    dead: VelocityTierCount

class CategoryPerformanceItem(BaseModel):
    category: str
    sku_count: int
    current_stock: float
    total_inventory_value: float
    units_sold: float
    cogs: float
    turnover_ratio: float
    average_dsi: Optional[float]

class IngestionResult(BaseModel):
    success: bool
    message: str
    rows_processed: int
    products_created_or_updated: int
    transactions_recorded: int
    min_date: Optional[str]
    max_date: Optional[str]
