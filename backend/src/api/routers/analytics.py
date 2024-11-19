# backend/src/api/routers/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, timedelta
from ..dependencies import get_db
from database.utils import DatabaseManager
from pydantic import BaseModel

router = APIRouter()

class SpendingAnalysis(BaseModel):
    total_spending: float
    by_category: Dict[str, float]
    top_merchants: List[Dict[str, float]]
    monthly_trend: List[Dict[str, float]]

@router.get("/spending-analysis")
async def get_spending_analysis(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """Get comprehensive spending analysis."""
    try:
        # Get spending by category
        spending = await DatabaseManager.get_spending_by_category(
            db=db,
            user_id=1,  # TODO: Get from auth
            start_date=start_date,
            end_date=end_date
        )
        
        # Get transactions for merchant analysis
        transactions = await DatabaseManager.get_transactions_by_date_range(
            db=db,
            user_id=1,  # TODO: Get from auth
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate total spending
        total_spending = sum(spending.values())
        
        # Get top merchants
        merchant_spending = {}
        for receipt in transactions["receipts"]:
            if receipt.store_name not in merchant_spending:
                merchant_spending[receipt.store_name] = 0
            merchant_spending[receipt.store_name] += receipt.total
        
        top_merchants = sorted(
            [{"merchant": k, "amount": v} for k, v in merchant_spending.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]
        
        # Calculate monthly trend
        monthly_trend = []
        current_date = start_date
        while current_date <= end_date:
            month_end = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            month_spending = await DatabaseManager.get_spending_by_category(
                db=db,
                user_id=1,  # TODO: Get from auth
                start_date=current_date,
                end_date=month_end
            )
            monthly_trend.append({
                "month": current_date.strftime("%Y-%m"),
                "total": sum(month_spending.values())
            })
            current_date = (current_date + timedelta(days=32)).replace(day=1)
        
        return SpendingAnalysis(
            total_spending=total_spending,
            by_category=spending,
            top_merchants=top_merchants,
            monthly_trend=monthly_trend
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))