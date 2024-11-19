# backend/src/tools/generate_sample_receipt.py
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from pathlib import Path

def generate_sample_receipt():
    # Create a white image
    width = 400
    height = 800
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a monospace font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Courier.dfont", 20)
    except:
        font = ImageFont.load_default()
    
    # Sample receipt content
    store_name = "GROCERY STORE"
    date = datetime.now().strftime("%m/%d/%Y")
    items = [
        ("Milk 1L", 3.99),
        ("Bread", 2.49),
        ("Eggs 12pk", 4.99),
        ("Bananas", 1.99),
        ("Coffee", 7.99)
    ]
    
    # Draw receipt content
    y_position = 50
    
    # Store name
    draw.text((width//4, y_position), store_name, font=font, fill='black')
    y_position += 40
    
    # Date
    draw.text((width//4, y_position), date, font=font, fill='black')
    y_position += 40
    
    # Items
    draw.line((50, y_position, width-50, y_position), fill='black')
    y_position += 20
    
    subtotal = 0
    for item, price in items:
        text = f"{item:<15} ${price:>5.2f}"
        draw.text((50, y_position), text, font=font, fill='black')
        y_position += 30
        subtotal += price
    
    # Total
    y_position += 20
    draw.line((50, y_position, width-50, y_position), fill='black')
    y_position += 20
    tax = subtotal * 0.08
    total = subtotal + tax
    
    draw.text((50, y_position), f"Subtotal: ${subtotal:>6.2f}", font=font, fill='black')
    y_position += 30
    draw.text((50, y_position), f"Tax:      ${tax:>6.2f}", font=font, fill='black')
    y_position += 30
    draw.text((50, y_position), f"Total:    ${total:>6.2f}", font=font, fill='black')
    
    # Save the image
    current_dir = Path(__file__).parent
    samples_dir = current_dir.parent / 'tests' / 'samples'
    samples_dir.mkdir(parents=True, exist_ok=True)
    image_path = samples_dir / 'sample_receipt.jpg'
    
    # Add some noise and blur to make it more realistic
    cv_image = np.array(image)
    cv_image = cv2.GaussianBlur(cv_image, (3, 3), 0)
    noise = np.random.normal(0, 2, cv_image.shape).astype(np.uint8)
    cv_image = cv2.add(cv_image, noise)
    
    cv2.imwrite(str(image_path), cv_image)
    return str(image_path)

if __name__ == "__main__":
    image_path = generate_sample_receipt()
    print(f"Generated sample receipt at: {image_path}")

""" 
    To test the complete OCR pipeline:

    1. First, generate a sample receipt:
    # From the backend/src directory
    python tools/generate_sample_receipt.py
    

    2. Then process it with the test tool:
    python tools/test_receipt.py tests/samples/sample_receipt.jpg """
