# backend/src/api/routers/budgets.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..dependencies import get_db
from database.utils import DatabaseManager
from database.models import Budget, CategoryType
from pydantic import BaseModel

router = APIRouter()

class BudgetCreate(BaseModel):
    category: CategoryType
    amount: float
    start_date: datetime
    end_date: datetime

class BudgetResponse(BudgetCreate):
    id: int
    current_spending: float
    remaining: float

@router.post("/create", response_model=BudgetResponse)
async def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db)
):
    """Create a new budget for a category."""
    try:
        stored_budget = Budget(
            user_id=1,  # TODO: Get from auth
            category=budget.category,
            amount=budget.amount,
            start_date=budget.start_date,
            end_date=budget.end_date
        )
        db.add(stored_budget)
        db.commit()
        db.refresh(stored_budget)
        
        # Get current spending for this category
        spending = await DatabaseManager.get_spending_by_category(
            db=db,
            user_id=1,  # TODO: Get from auth
            start_date=budget.start_date,
            end_date=budget.end_date
        )
        
        current_spending = spending.get(budget.category.value, 0)
        
        return {
            **budget.dict(),
            "id": stored_budget.id,
            "current_spending": current_spending,
            "remaining": budget.amount - current_spending
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
