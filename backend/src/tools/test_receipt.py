# backend/src/tools/test_receipt.py
import cv2
import asyncio
import argparse
from pathlib import Path
import sys
import os
from rich.console import Console
from rich.table import Table

console = Console()

async def process_receipt_image(image_path: str, debug: bool = True):
    """Process a receipt image and display the results with debug information."""
    try:
        # Load and process image
        console.print(f"\nProcessing receipt: {image_path}", style="blue")
        
        image = cv2.imread(image_path)
        if image is None:
            console.print("Failed to load image!", style="red bold")
            return
            
        # Show image details if in debug mode
        if debug:
            console.print(f"\nImage size: {image.shape}", style="yellow")
        
        # Initialize services
        from services.ocr.service import OCRService
        ocr_service = OCRService()
        
        # Process receipt
        console.print("\nExtracting text...", style="yellow")
        receipt_data = await ocr_service.process_receipt(image)
        
        if receipt_data is None:
            console.print("Failed to process receipt!", style="red bold")
            return
            
        # Display results
        console.print("\n=== Receipt Details ===", style="bold green")
        console.print(f"Store: {receipt_data.store_name}", style="green")
        console.print(f"Date: {receipt_data.date.strftime('%Y-%m-%d %H:%M')}", style="green")
        
        # Create items table
        items_table = Table(show_header=True, header_style="bold magenta")
        items_table.add_column("Item")
        items_table.add_column("Price", justify="right")
        items_table.add_column("Qty", justify="right")
        items_table.add_column("Total", justify="right")
        
        for item in receipt_data.items:
            items_table.add_row(
                item.description,
                f"${item.price:.2f}",
                str(item.quantity),
                f"${item.price * item.quantity:.2f}"
            )
        
        console.print("\nItemized List:")
        console.print(items_table)
        
        # Display totals
        console.print("\nTotals:", style="bold blue")
        console.print(f"Subtotal: ${receipt_data.subtotal:.2f}", style="blue")
        console.print(f"Tax: ${receipt_data.tax:.2f}", style="blue")
        console.print(f"Total: ${receipt_data.total:.2f}", style="bold blue")
        
    except Exception as e:
        console.print(f"\nError during processing: {str(e)}", style="red bold")
        if debug:
            import traceback
            console.print(traceback.format_exc(), style="red")

def main():
    parser = argparse.ArgumentParser(description="Test receipt processing")
    parser.add_argument("image_path", help="Path to the receipt image")
    parser.add_argument("--no-debug", action="store_true", help="Disable debug output")
    args = parser.parse_args()
    
    asyncio.run(process_receipt_image(args.image_path, not args.no_debug))

if __name__ == "__main__":
    main()