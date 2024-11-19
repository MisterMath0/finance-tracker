# backend/src/services/categorization/categories.py
from enum import Enum

class ExpenseCategory(str, Enum):
    GROCERIES = "groceries"
    HOUSEHOLD = "household"
    HEALTH_BEAUTY = "health_and_beauty"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    ENTERTAINMENT = "entertainment"
    DINING = "dining"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    MISCELLANEOUS = "miscellaneous"