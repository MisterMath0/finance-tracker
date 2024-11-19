# backend/src/api/routes/expenses.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from datetime import datetime, timedelta
from ..dependencies import get_settings
from services.categorization.classifier import ExpenseClassifier
from services.categorization.budget_tracker import BudgetTracker
from services.categorization.categories import ExpenseCategory
from pydantic import BaseModel

router = APIRouter()
budget_tracker = BudgetTracker()  # This will be moved to a proper database later

class BudgetLimitRequest(BaseModel):
    category: ExpenseCategory
    amount: float
    period: str

@router.post("/categorize")
async def categorize_receipt(receipt_id: str):
    """Categorize a processed receipt and add it to budget tracking."""
    try:
        # In a real implementation, we would fetch the receipt from database
        # For now, we'll use our test receipt
        receipt = get_test_receipt()  
        
        settings = get_settings()
        classifier = ExpenseClassifier(settings.OPENAI_API_KEY)
        
        # Categorize the receipt
        categorized_data = await classifier.categorize_receipt(receipt)
        
        # Add to budget tracker
        budget_tracker.add_expense(categorized_data)
        
        return categorized_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/budget/set-limit")
async def set_budget_limit(budget: BudgetLimitRequest):
    """Set a budget limit for a category."""
    try:
        budget_tracker.set_budget_limit(
            category=budget.category,
            amount=budget.amount,
            period=budget.period
        )
        return {"message": f"Budget limit set for {budget.category.value}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/budget/status")
async def get_budget_status(
    start_date: datetime = None,
    end_date: datetime = None
):
    """Get budget status for all categories."""
    try:
        # Default to current month if dates not provided
        if not start_date:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        if not end_date:
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        status = budget_tracker.get_status(start_date, end_date)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))