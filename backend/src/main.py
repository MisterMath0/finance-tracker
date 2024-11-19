# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import receipts, statements, budgets, analytics

app = FastAPI(
    title="Finance Tracker API",
    description="API for managing receipts, bank statements, and budgets",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(receipts, prefix="/api/receipts", tags=["receipts"])
app.include_router(statements, prefix="/api/statements", tags=["statements"])
app.include_router(budgets, prefix="/api/budgets", tags=["budgets"])
app.include_router(analytics, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
async def root():
    return {"message": "Finance Tracker API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)