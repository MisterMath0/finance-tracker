# backend/src/database/setup_db.py
import sys
import subprocess
from pathlib import Path
from rich.console import Console
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import os

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

load_dotenv()

console = Console()

def setup_database():
    """Set up PostgreSQL databases for development and testing."""
    # Database configuration
    user = os.getenv("POSTGRES_USER", "admin")
    password = os.getenv("POSTGRES_PASSWORD", "admin")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    main_db = os.getenv("POSTGRES_DB", "finance_tracker")
    test_db = "finance_tracker_test"

    console.print("\n=== Setting up PostgreSQL Databases ===\n", style="bold blue")

    try:
        # Connect to PostgreSQL server
        console.print("Connecting to PostgreSQL server...", style="yellow")
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres"  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Create main database if it doesn't exist
        console.print(f"\nChecking main database '{main_db}'...", style="yellow")
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{main_db}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE {main_db}")
            console.print(f"✓ Created database '{main_db}'", style="green")
        else:
            console.print(f"Database '{main_db}' already exists", style="blue")

        # Create test database if it doesn't exist
        console.print(f"\nChecking test database '{test_db}'...", style="yellow")
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{test_db}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE {test_db}")
            console.print(f"✓ Created database '{test_db}'", style="green")
        else:
            console.print(f"Database '{test_db}' already exists", style="blue")

        cursor.close()
        conn.close()

        # Initialize tables for both databases
        from database.init_db import initialize_database
        
        console.print("\nInitializing main database...", style="yellow")
        initialize_database(testing=False)
        
        console.print("\nInitializing test database...", style="yellow")
        initialize_database(testing=True)

        console.print("\n[bold green]Database setup completed successfully![/]")
        
        # Show connection information
        console.print("\nConnection Information:", style="yellow")
        console.print(f"Host: {host}")
        console.print(f"Port: {port}")
        console.print(f"User: {user}")
        console.print(f"Main Database: {main_db}")
        console.print(f"Test Database: {test_db}")

    except Exception as e:
        console.print(f"\n[bold red]Error setting up database: {str(e)}[/]")
        
        # Provide troubleshooting steps
        console.print("\nTroubleshooting steps:", style="yellow")
        console.print("1. Verify PostgreSQL is running:")
        console.print("   brew services list")
        console.print("\n2. Check PostgreSQL connection:")
        console.print(f"   psql -U {user} -h {host} -p {port} postgres")
        console.print("\n3. Verify user permissions:")
        console.print(f"   psql -U {user} -d postgres -c '\\du'")
        console.print("\n4. Check your .env file configuration")
        raise

if __name__ == "__main__":
    setup_database()