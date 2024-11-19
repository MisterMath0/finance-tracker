# backend/src/api/routers/statements.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from services.pdf_processing.statement_extractor import StatementProcessor
from database.utils import DatabaseManager

router = APIRouter()
statement_processor = StatementProcessor()

@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a bank statement PDF."""
    try:
        # Save PDF temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process statement
        transactions = await statement_processor.process_statement(temp_path)
        
        # Store transactions
        stored_transactions = []
        for transaction in transactions:
            stored_transaction = await DatabaseManager.create_bank_transaction(
                db=db,
                user_id=1,  # TODO: Get from auth
                date=transaction.date,
                description=transaction.description,
                amount=transaction.amount,
                transaction_type=transaction.transaction_type,
                category=transaction.category,
                raw_text=transaction.raw_text
            )
            stored_transactions.append(stored_transaction)
        
        return {"message": f"Processed {len(stored_transactions)} transactions"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
