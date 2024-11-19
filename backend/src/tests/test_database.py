# backend/src/tests/test_database.py
import sys
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# Load test environment variables
load_dotenv()

from database.config import get_engine, get_session_maker, init_db
from database.models import Base, User, Receipt, ReceiptItem, BankTransaction, Budget, CategoryType, TransactionType
from database.utils import DatabaseManager
from database.init_db import initialize_database

console = Console()

async def setup_test_database():
    """Initialize test database."""
    console.print("\n=== Setting up Test Database ===\n", style="bold blue")
    
    # Get engine and initialize database
    engine = get_engine(testing=True)
    
    # Drop all tables if they exist
    console.print("Dropping existing tables...", style="yellow")
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    console.print("Creating fresh tables...", style="yellow")
    Base.metadata.create_all(bind=engine)
    
    console.print("✓ Test database setup complete!", style="green")

async def test_database_operations():
    """Test all database operations."""
    # Setup test database
    await setup_test_database()
    
    console.print("\n=== Running Database Tests ===\n", style="bold blue")
    
    # Get test session maker
    TestingSessionLocal = get_session_maker(testing=True)
    
    try:
        # Rest of your test code remains the same...
        with TestingSessionLocal() as db:
            # Your existing test code here...
            pass
            
    except Exception as e:
        console.print(f"\n[bold red]Error during testing: {str(e)}[/]")
        import traceback
        console.print(traceback.format_exc(), style="red")
        raise

if __name__ == "__main__":
    asyncio.run(test_database_operations())