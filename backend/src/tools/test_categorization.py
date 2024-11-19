# backend/src/tools/test_categorization.py
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# Load environment variables
load_dotenv()

from services.categorization.classifier import ExpenseClassifier
from services.ocr.extractor import Receipt, ReceiptItem
from services.categorization.categories import ExpenseCategory

console = Console()

# Sample Target receipt data based on your OCR results
def create_test_receipt():
    items = [
        ReceiptItem("UPUP HOUSEH", 1.94, 1),
        ReceiptItem("OREO COOKIE", 5.98, 2),
        ReceiptItem("NATVAL ENER", 5.89, 1),
        ReceiptItem("MOTTS FRTSN", 1.50, 3),
        ReceiptItem("V8", 4.19, 1),
        ReceiptItem("OSCAR MAYER", 2.50, 1),
        ReceiptItem("TOMATO", 0.99, 1),
        ReceiptItem("LETTUCE", 1.49, 1),
        ReceiptItem("KC MASTERPC", 3.39, 1),
        ReceiptItem("MARKET PANT", 3.29, 1),
        ReceiptItem("PEPPERIDGE", 2.99, 1),
        ReceiptItem("SMUCKERS", 2.09, 1),
        ReceiptItem("JENNIE-O", 2.99, 1),
        ReceiptItem("LEAN CUISIN", 2.45, 4),
        ReceiptItem("EVOL", 5.59, 1),
        ReceiptItem("BIRD SUBB H", 4.09, 1),
        ReceiptItem("CHOBANI", 1.00, 4),
        ReceiptItem("BREYERS", 3.49, 2),
        ReceiptItem("AQUAF 2PK", 4.89, 1),
        ReceiptItem("SONICARE", 21.99, 1),
        ReceiptItem("BISSELL", 129.99, 1),
    ]

    return Receipt(
        store_name="TARGET",
        date=datetime(2016, 3, 6, 17, 25),
        items=items,
        total=251.83,
        subtotal=246.00,
        tax=5.83,
        raw_text=""
    )

async def test_categorization():
    console.print("\n=== Testing Receipt Categorization ===\n", style="bold blue")
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("Error: OPENAI_API_KEY not found in environment variables", style="bold red")
        return

    try:
        # Initialize classifier
        classifier = ExpenseClassifier(api_key)
        
        # Create test receipt
        receipt = create_test_receipt()
        
        console.print("Processing receipt...", style="yellow")
        result = await classifier.categorize_receipt(receipt)
        
        # Display results
        console.print("\nCategorization Results:", style="bold green")
        
        # Create a summary table
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Category")
        summary_table.add_column("Total", justify="right")
        summary_table.add_column("% of Total", justify="right")
        
        grand_total = sum(cat_data["total"] for cat_data in result["categories"].values())
        
        for category, data in result["categories"].items():
            if data["total"] > 0:
                percentage = (data["total"] / grand_total) * 100
                summary_table.add_row(
                    category.replace("_", " ").title(),
                    f"${data['total']:.2f}",
                    f"{percentage:.1f}%"
                )
        
        console.print("\nExpense Summary:")
        console.print(summary_table)
        
        # Display detailed breakdown
        console.print("\nDetailed Breakdown:", style="bold blue")
        
        for category, data in result["categories"].items():
            if data["items"]:
                console.print(f"\n{category.replace('_', ' ').title()}:", style="bold yellow")
                
                items_table = Table(show_header=True, header_style="bold cyan")
                items_table.add_column("Item")
                items_table.add_column("Price", justify="right")
                items_table.add_column("Qty", justify="right")
                items_table.add_column("Total", justify="right")
                items_table.add_column("Reason")
                
                for item in data["items"]:
                    items_table.add_row(
                        item["description"],
                        f"${item['price']:.2f}",
                        str(item["quantity"]),
                        f"${item['total']:.2f}",
                        item["reason"]
                    )
                
                console.print(items_table)
        
        # Print receipt totals
        console.print("\nReceipt Totals:", style="bold green")
        console.print(f"Subtotal: ${result['total']:.2f}")
        console.print(f"Tax: ${result['tax']:.2f}")
        console.print(f"Total: ${grand_total + result['tax']:.2f}")
        
    except Exception as e:
        console.print(f"\nError: {str(e)}", style="bold red")
        import traceback
        console.print(traceback.format_exc(), style="red")

if __name__ == "__main__":
    asyncio.run(test_categorization())