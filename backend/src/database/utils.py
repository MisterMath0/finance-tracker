# backend/src/database/utils.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Receipt, ReceiptItem, BankTransaction, Budget, CategoryType

class DatabaseManager:
    @staticmethod
    async def create_receipt(
        db: Session,
        user_id: int,
        store_name: str,
        date: datetime,
        items: List[Dict[str, Any]],
        subtotal: float,
        tax: float,
        total: float,
        raw_text: Optional[str] = None
    ) -> Receipt:
        """Create a new receipt with items."""
        try:
            # Create receipt
            receipt = Receipt(
                user_id=user_id,
                store_name=store_name,
                date=date,
                subtotal=subtotal,
                tax=tax,
                total=total,
                raw_text=raw_text
            )
            db.add(receipt)
            db.flush()

            # Create receipt items
            for item in items:
                receipt_item = ReceiptItem(
                    receipt_id=receipt.id,
                    description=item["description"],
                    quantity=item.get("quantity", 1),
                    price=item["price"],
                    category=item["category"]
                )
                db.add(receipt_item)

            # Commit the transaction
            db.commit()
            db.refresh(receipt)
            return receipt

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    async def get_receipts(
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Receipt]:
        """Get receipts with optional date filtering."""
        query = db.query(Receipt).filter(Receipt.user_id == user_id)
        
        if start_date:
            query = query.filter(Receipt.date >= start_date)
        if end_date:
            query = query.filter(Receipt.date <= end_date)
            
        return query.all()

    @staticmethod
    async def get_receipt(db: Session, receipt_id: int) -> Optional[Receipt]:
        """Get a specific receipt by ID."""
        return db.query(Receipt).filter(Receipt.id == receipt_id).first()

    @staticmethod
    async def get_receipt_categories_summary(
        db: Session,
        receipt_id: int
    ) -> Dict[str, Dict[str, float]]:
        """Get category summary for a receipt."""
        items = db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt_id).all()
        
        summary = {}
        for item in items:
            category = item.category.value
            if category not in summary:
                summary[category] = {
                    "total": 0,
                    "count": 0
                }
            summary[category]["total"] += item.price * item.quantity
            summary[category]["count"] += item.quantity
            
        return summary