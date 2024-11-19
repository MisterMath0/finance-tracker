# backend/src/services/ocr/service.py
from .preprocessing import ImagePreprocessor
from .extractor import ReceiptExtractor, Receipt
from ..categorization.classifier import ExpenseClassifier
import numpy as np
from typing import Optional
import os
from rich.console import Console

console = Console()

class OCRService:
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.extractor = ReceiptExtractor()
        self.classifier = ExpenseClassifier(
            api_key=os.getenv("OPENAI_API_KEY")
        )

    async def process_receipt(self, image: np.ndarray) -> Optional[Receipt]:
        """Process receipt image with LLM-based classification."""
        try:
            console.print("\n=== Processing Receipt ===", style="bold blue")
            
            # Preprocess image
            console.print("Preprocessing image...", style="yellow")
            preprocessed = self.preprocessor.preprocess_receipt(image)
            
            # Extract text
            console.print("Extracting text...", style="yellow")
            text = self.extractor.extract_text(preprocessed)
            
            if not text.strip():
                console.print("[red]No text extracted from image")
                return None

            # Extract receipt data
            console.print("Parsing receipt data...", style="yellow")
            receipt_data = self.extractor.extract_receipt_data(text)
            
            # Classify items
            console.print("Classifying items...", style="yellow")
            classified_items = await self.classifier.classify_items(
                items=[{
                    "description": item.description,
                    "price": item.price
                } for item in receipt_data.items],
                store_name=receipt_data.store_name,
                total_amount=receipt_data.total
            )
            
            # Update items with categories
            console.print("\nClassification Results:", style="bold green")
            for item, classified in zip(receipt_data.items, classified_items):
                item.category = classified.category
                console.print(
                    f"Item: {classified.description}\n"
                    f"Category: {classified.category.value}\n"
                    f"Confidence: {classified.confidence:.2f}\n"
                    f"Reasoning: {classified.reasoning}\n"
                )
            
            return receipt_data

        except Exception as e:
            console.print(f"[red]Error processing receipt: {str(e)}")
            return None