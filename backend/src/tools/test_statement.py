# backend/src/tools/test_statement.py
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

# Load environment variables
load_dotenv()

from services.pdf_processing.statement_extractor import StatementProcessor

console = Console()

async def process_bank_statement(pdf_path: str):
    """Process and display results from a bank statement PDF."""
    console.print("\n=== Processing Bank Statement ===\n", style="bold blue")
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("Error: OPENAI_API_KEY not found in environment variables", style="bold red")
        return
    
    try:
        # Initialize processor
        processor = StatementProcessor()
        
        # Process statement
        console.print("Extracting transactions...", style="yellow")
        transactions = await processor.process_statement(pdf_path, api_key)
        
        # Display results
        console.print(f"\nFound {len(transactions)} transactions", style="green")
        
        # Create transaction table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date")
        table.add_column("Description")
        table.add_column("Amount", justify="right")
        table.add_column("Type")
        table.add_column("Category")
        
        # Group transactions by category for summary
        category_totals = {}
        
        for transaction in transactions:
            # Add to table
            table.add_row(
                transaction.date.strftime("%Y-%m-%d"),
                transaction.description,
                f"${transaction.amount:.2f}",
                transaction.transaction_type,
                transaction.category or "Uncategorized"
            )
            
            # Add to category totals
            category = transaction.category or "Uncategorized"
            if category not in category_totals:
                category_totals[category] = 0.0
            if transaction.transaction_type == 'debit':
                category_totals[category] += transaction.amount
        
        console.print("\nTransactions:")
        console.print(table)
        
        # Display category summary
        summary_table = Table(show_header=True, header_style="bold cyan")
        summary_table.add_column("Category")
        summary_table.add_column("Total Spent", justify="right")
        summary_table.add_column("% of Total", justify="right")
        
        total_spent = sum(amount for amount in category_totals.values())
        
        for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            if amount > 0:  # Only show categories with spending
                percentage = (amount / total_spent * 100) if total_spent > 0 else 0
                summary_table.add_row(
                    category.replace('_', ' ').title(),
                    f"${amount:.2f}",
                    f"{percentage:.1f}%"
                )
        
        console.print("\nSpending Summary:")
        console.print(summary_table)
        
    except Exception as e:
        console.print(f"\nError: {str(e)}", style="bold red")
        import traceback
        console.print(traceback.format_exc(), style="red")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process bank statement PDF")
    parser.add_argument("pdf_path", help="Path to the bank statement PDF")
    args = parser.parse_args()
    
    asyncio.run(process_bank_statement(args.pdf_path))

if __name__ == "__main__":
    main()