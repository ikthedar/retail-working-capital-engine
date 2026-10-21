from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True, default="")
    sub_category = Column(String, index=True, default="")
    tool_type = Column(String, index=True, default="")
    sub_type = Column(String, index=True, default="")
    product_name = Column(String, index=True, nullable=False)
    unit_cost = Column(Float, default=0.0)
    current_stock = Column(Float, default=0.0)
    total_value = Column(Float, default=0.0)
    supplier_name = Column(String, index=True, default="Unknown")
    created_at = Column(DateTime, server_default=func.now())

    transactions = relationship("Transaction", back_populates="product", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    transaction_date = Column(Date, index=True, nullable=False)
    transaction_type = Column(String, index=True, nullable=False)  # 'SALE', 'PURCHASE', 'SHRINKAGE'
    quantity = Column(Float, nullable=False)
    unit = Column(String, default="pc")
    unit_cost = Column(Float, default=0.0)
    supplier_name = Column(String, index=True, default="Unknown")
    raw_text = Column(String, default="")

    product = relationship("Product", back_populates="transactions")
