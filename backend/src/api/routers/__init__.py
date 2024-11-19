# backend/src/api/routers/__init__.py
from fastapi import APIRouter

# Import routers
from .receipts import router as receipts_router

# Create empty routers for now
statements_router = APIRouter()
budgets_router = APIRouter()
analytics_router = APIRouter()

# Export routers
receipts = receipts_router
statements = statements_router
budgets = budgets_router
analytics = analytics_router