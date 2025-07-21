from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property


Base = declarative_base()
engine = create_engine('sqlite:///receipts.db', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class CategoryEnum(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    HEALTH = "Health"
    OTHER = "Other"

class VendorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: Optional[CategoryEnum] = None

class VendorCreate(VendorBase):
    pass

class Vendor(VendorBase):
    id: int
    
    class Config:
        orm_mode = True

class BillEntryBase(BaseModel):
    vendor_id: int
    amount: float = Field(..., gt=0)
    transaction_date: Optional[date] = None
    description: Optional[str] = None
    file_reference: Optional[str] = None

    @validator('transaction_date')
    def date_not_in_future(cls, v):
        if v and v > date.today():
            raise ValueError("Transaction date cannot be in the future")
        return v


class BillEntryCreate(BillEntryBase):
    pass

class BillEntry(BillEntryBase):
    id: int
    vendor: Vendor
    
    class Config:
        orm_mode = True

class DBCategory(Base):
    """Optional normalized category table"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

class DBVendor(Base):
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)
    
    bills = relationship("DBBillEntry", back_populates="vendor")
    
    @hybrid_property
    def total_spent(self):
        return sum(bill.amount for bill in self.bills)

class DBBillEntry(Base):
    __tablename__ = 'bill_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), index=True)
    amount = Column(Float, nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(String(1000000))
    file_reference = Column(String(500)) 
    
    vendor = relationship("DBVendor", back_populates="bills")

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")