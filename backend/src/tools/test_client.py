# backend/src/tests/test_client.py
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

async def test_receipt_upload(image_path: str):
    """Test receipt upload and processing."""
    console.print("\n=== Testing Receipt Upload ===\n", style="bold blue")
    
    async with aiohttp.ClientSession() as session:
        # Upload receipt
        console.print("Uploading receipt...", style="yellow")
        
        data = aiohttp.FormData()
        async with aiofiles.open(image_path, 'rb') as f:
            data.add_field('file',
                          await f.read(),
                          filename=Path(image_path).name,
                          content_type='image/jpeg')
        
        async with session.post('http://localhost:8000/api/receipts/upload', data=data) as response:
            result = await response.json()
            
            if response.status == 200:
                console.print("✓ Receipt uploaded successfully!", style="green")
                
                # Display receipt details
                console.print("\nReceipt Details:", style="bold blue")
                console.print(f"Store: {result['store_name']}")
                console.print(f"Date: {result['date']}")
                console.print(f"Total: ${result['total']:.2f}")
                
                # Display items table
                items_table = Table(show_header=True)
                items_table.add_column("Item")
                items_table.add_column("Quantity", justify="right")
                items_table.add_column("Price", justify="right")
                items_table.add_column("Total", justify="right")
                items_table.add_column("Category")
                
                for item in result['items']:
                    items_table.add_row(
                        item['description'],
                        str(item['quantity']),
                        f"${item['price']:.2f}",
                        f"${item['price'] * item['quantity']:.2f}",
                        item['category']
                    )
                
                console.print("\nItemized List:")
                console.print(items_table)
                
                # Display categories summary
                categories_table = Table(show_header=True)
                categories_table.add_column("Category")
                categories_table.add_column("Items", justify="right")
                categories_table.add_column("Total", justify="right")
                
                for category, data in result['categories_summary'].items():
                    categories_table.add_row(
                        category.replace('_', ' ').title(),
                        str(data['count']),
                        f"${data['total']:.2f}"
                    )
                
                console.print("\nCategories Summary:")
                console.print(categories_table)
            else:
                console.print(f"✗ Error: {result}", style="red")

async def main():
    # Test receipt upload
    await test_receipt_upload('tests/samples/real_receipt.jpg')  # Update with your receipt path

if __name__ == "__main__":
    asyncio.run(main())