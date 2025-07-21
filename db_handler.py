from sqlalchemy import exc, func, or_
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict, Generator
from datetime import date
import logging
from models import Base, DBVendor, DBBillEntry, SessionLocal, engine, CategoryEnum
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self):
        self._create_tables()
    
    def _create_tables(self) -> None:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables initialized")
        except exc.SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def get_db(self) -> Generator[Session, None, None]:
        db = SessionLocal()
        try:
            yield db
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            db.close()


    def add_vendor(self, vendor_data: Dict) -> Tuple[bool, DBVendor]:
        with SessionLocal() as db:
            try:
                if vendor_data.get("category") and not isinstance(vendor_data["category"], str):
                    vendor_data["category"] = str(vendor_data["category"])
                existing = db.query(DBVendor).filter(
                    func.lower(DBVendor.name) == func.lower(vendor_data["name"])
                ).first()
                if existing:
                    if vendor_data.get("category") and existing.category != vendor_data["category"]:
                        existing.category = vendor_data["category"]
                        db.commit()
                        db.refresh(existing)
                    return False, existing
                vendor = DBVendor(**vendor_data)
                db.add(vendor)
                db.commit()
                db.refresh(vendor)
                return True, vendor
            except exc.SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error adding vendor: {e}")
                raise

    def get_vendor(self, vendor_id: int) -> Optional[DBVendor]:
        with SessionLocal() as db:
            return db.query(DBVendor).filter(DBVendor.id == vendor_id).first()

    def search_vendors(self, search_term: str) -> List[DBVendor]:
        with SessionLocal() as db:
            return db.query(DBVendor).filter(
                DBVendor.name.ilike(f"%{search_term}%")
            ).all()

    def add_bill(self, bill_data: Dict) -> DBBillEntry:
        """Add bill entry with transaction"""
        with SessionLocal() as db:
            try:
                bill = DBBillEntry(**bill_data)
                db.add(bill)
                db.commit()
                db.refresh(bill)
                return bill
            except exc.SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error adding bill: {e}")
                raise

    

    def get_bills(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        vendor_id: Optional[int] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[DBBillEntry]:
        with SessionLocal() as db:
            query = db.query(DBBillEntry).options(joinedload(DBBillEntry.vendor))
            if vendor_id:
                query = query.filter(DBBillEntry.vendor_id == vendor_id)
            if start_date:
                query = query.filter(DBBillEntry.transaction_date >= start_date)
            if end_date:
                query = query.filter(DBBillEntry.transaction_date <= end_date)
            if min_amount:
                query = query.filter(DBBillEntry.amount >= min_amount)
            if max_amount:
                query = query.filter(DBBillEntry.amount <= max_amount)
            if category:
                query = query.join(DBVendor).filter(DBVendor.category == category)
            return query.order_by(DBBillEntry.transaction_date.desc()).limit(limit).all()


    def update_bill(self, bill_id: int, update_data: Dict) -> Optional[DBBillEntry]:
        with SessionLocal() as db:
            try:
                bill = db.query(DBBillEntry).filter(DBBillEntry.id == bill_id).first()
                if not bill:
                    return None
                
                for key, value in update_data.items():
                    setattr(bill, key, value)
                
                db.commit()
                db.refresh(bill)
                return bill
            except exc.SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error updating bill: {e}")
                raise

    def delete_bill(self, bill_id: int) -> bool:
        with SessionLocal() as db:
            try:
                bill = db.query(DBBillEntry).filter(DBBillEntry.id == bill_id).first()
                if not bill:
                    return False
                
                db.delete(bill)
                db.commit()
                return True
            except exc.SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error deleting bill: {e}")
                raise

    # Analytics Operations
    def get_spending_by_category(self, start_date: date, end_date: date) -> List[Tuple[str, float]]:
        with SessionLocal() as db:
            return db.query(
                DBVendor.category,
                func.sum(DBBillEntry.amount).label('total')
            ).join(DBBillEntry).filter(
                DBBillEntry.transaction_date.between(start_date, end_date)
            ).group_by(DBVendor.category).all()

    def get_monthly_spending(self) -> List[Tuple[str, float]]:
        with SessionLocal() as db:
            return db.query(
                func.strftime("%Y-%m", DBBillEntry.transaction_date).label('month'),
                func.sum(DBBillEntry.amount).label('total')
            ).group_by('month').order_by('month').all()

    def get_vendor_by_name(self, vendor_name: str) -> Optional[DBVendor]:
        with SessionLocal() as db:
            return db.query(DBVendor).filter(
                func.lower(DBVendor.name) == func.lower(vendor_name.strip())
            ).first()

    def create_vendor(self, vendor_name: str) -> DBVendor:
        with SessionLocal() as db:
            vendor = DBVendor(name=vendor_name.strip())
            db.add(vendor)
            db.commit()
            db.refresh(vendor)
            return vendor

