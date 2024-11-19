# backend/src/database/init_db.py
import sys
from pathlib import Path
from rich.console import Console

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from database.config import engine, SessionLocal, Base
from database.user_utils import UserManager

console = Console()

def initialize_database():
    """Initialize database with tables and test user."""
    try:
        console.print("\n=== Initializing Database ===\n", style="bold blue")
        
        # Create all tables
        console.print("Creating database tables...", style="yellow")
        Base.metadata.create_all(bind=engine)
        
        # Create test user
        console.print("Setting up test user...", style="yellow")
        with SessionLocal() as db:
            test_user = UserManager.create_test_user(db)
            console.print(f"✓ Test user created/verified (ID: {test_user.id})", style="green")
        
        console.print("\n✓ Database initialized successfully!", style="green")
        
    except Exception as e:
        console.print(f"\n[bold red]Error initializing database: {str(e)}[/]")
        raise

if __name__ == "__main__":
    initialize_database()