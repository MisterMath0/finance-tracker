# backend/src/services/categorization/budget_tracker.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from .categories import ExpenseCategory

@dataclass
class BudgetLimit:
    category: ExpenseCategory
    amount: float
    period: str  # 'monthly', 'weekly', etc.

@dataclass
class BudgetStatus:
    category: ExpenseCategory
    limit: float
    spent: float
    remaining: float
    percent_used: float

class BudgetTracker:
    def __init__(self):
        self.budget_limits: Dict[ExpenseCategory, BudgetLimit] = {}
        self.expenses: List[Dict] = []  # Will be replaced with database

    def set_budget_limit(self, category: ExpenseCategory, amount: float, period: str = 'monthly'):
        """Set a budget limit for a category."""
        self.budget_limits[category] = BudgetLimit(
            category=category,
            amount=amount,
            period=period
        )

    def add_expense(self, categorized_receipt: Dict):
        """Add a categorized receipt to the expense tracker."""
        self.expenses.append({
            "date": datetime.fromisoformat(categorized_receipt["date"]),
            "categories": categorized_receipt["categories"],
            "total": categorized_receipt["total"]
        })

    def get_status(self, start_date: datetime, end_date: datetime) -> Dict[str, BudgetStatus]:
        """Get budget status for all categories within a date range."""
        status = {}
        
        # Initialize status for all categories
        for category in ExpenseCategory:
            budget_limit = self.budget_limits.get(category)
            limit_amount = budget_limit.amount if budget_limit else 0
            
            status[category.value] = BudgetStatus(
                category=category,
                limit=limit_amount,
                spent=0,
                remaining=limit_amount,
                percent_used=0
            )

        # Calculate spent amounts
        for expense in self.expenses:
            if start_date <= expense["date"] <= end_date:
                for category, data in expense["categories"].items():
                    if category in status:
                        status[category].spent += data["total"]
        
        # Update remaining and percent used
        for category_status in status.values():
            if category_status.limit > 0:
                category_status.remaining = max(0, category_status.limit - category_status.spent)
                category_status.percent_used = (category_status.spent / category_status.limit) * 100
        
        return status