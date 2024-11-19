# backend/src/api/routers/receipts.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import cv2
import numpy as np
from pydantic import BaseModel

# Import from our application
from api.dependencies import get_database
from services.ocr.service import OCRService
from database.utils import DatabaseManager
from database.models import CategoryType
from database.user_utils import UserManager  # Add this import

router = APIRouter()
ocr_service = OCRService()

class ReceiptItem(BaseModel):
    description: str
    quantity: int
    price: float
    category: CategoryType

class ReceiptResponse(BaseModel):
    id: Optional[int]
    store_name: str
    date: datetime
    items: List[ReceiptItem]
    subtotal: float
    tax: float
    total: float
    categories_summary: dict

    class Config:
        orm_mode = True

@router.post("/upload", response_model=ReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_database)
):
    """Upload and process a receipt image."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Get test user
        test_user = UserManager.get_user_by_email(db, "test@example.com")
        if not test_user:
            test_user = UserManager.create_test_user(db)

        # Read and process image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Process receipt with OCR
        receipt_data = await ocr_service.process_receipt(image)
        if not receipt_data:
            raise HTTPException(status_code=422, detail="Failed to process receipt")

        # Store in database
        stored_receipt = await DatabaseManager.create_receipt(
            db=db,
            user_id=test_user.id,  # Use test user ID
            store_name=receipt_data.store_name,
            date=receipt_data.date,
            items=[{
                "description": item.description,
                "quantity": item.quantity,
                "price": item.price,
                "category": CategoryType.MISCELLANEOUS  # Default category
            } for item in receipt_data.items],
            subtotal=receipt_data.subtotal,
            tax=receipt_data.tax,
            total=receipt_data.total,
            raw_text=receipt_data.raw_text
        )

        # Calculate categories summary
        categories_summary = await DatabaseManager.get_receipt_categories_summary(
            db, stored_receipt.id
        )

        return ReceiptResponse(
            id=stored_receipt.id,
            store_name=stored_receipt.store_name,
            date=stored_receipt.date,
            items=[ReceiptItem(
                description=item.description,
                quantity=item.quantity,
                price=item.price,
                category=item.category
            ) for item in stored_receipt.items],
            subtotal=stored_receipt.subtotal,
            tax=stored_receipt.tax,
            total=stored_receipt.total,
            categories_summary=categories_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))