# backend/src/tests/test_db_connection.py
import sys
import os
from pathlib import Path
from rich.console import Console

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from database.config import get_engine, get_db
from sqlalchemy import text

console = Console()

def test_connection():
    """Test database connection."""
    console.print("\n=== Testing Database Connection ===\n", style="bold blue")
    
    try:
        # Get test engine
        engine = get_engine(testing=True)
        
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
            console.print("✓ Database connection successful!", style="green")
            
            # Show connection details
            console.print("\nConnection Details:", style="yellow")
            console.print(f"Database URL: {engine.url}", style="blue")
            console.print(f"Driver: {engine.driver}", style="blue")
            
            # Test database permissions
            console.print("\nTesting permissions...", style="yellow")
            connection.execute(text("CREATE TABLE IF NOT EXISTS test_table (id serial PRIMARY KEY)"))
            console.print("✓ Create table permission: OK", style="green")
            
            connection.execute(text("DROP TABLE test_table"))
            console.print("✓ Drop table permission: OK", style="green")
            
    except Exception as e:
        console.print(f"\n[bold red]Connection Error: {str(e)}[/]")
        console.print("\nTroubleshooting steps:", style="yellow")
        console.print("1. Verify PostgreSQL is running: brew services list")
        console.print("2. Check user permissions: psql -U admin -d postgres")
        console.print("3. Verify database exists: psql -U admin -d postgres -c '\\l'")
        raise

if __name__ == "__main__":
    test_connection()