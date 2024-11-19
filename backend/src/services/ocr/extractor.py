# backend/src/services/ocr/extractor.py
import pytesseract
from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime
import re

@dataclass
class ReceiptItem:
    description: str
    price: float
    quantity: Optional[int] = 1

@dataclass
class Receipt:
    store_name: str
    date: datetime
    items: List[ReceiptItem]
    total: float
    subtotal: float
    tax: float
    raw_text: str

class ReceiptExtractor:
    def __init__(self):
        # Enhanced patterns for better recognition
        self.price_pattern = r'\$?\d+\.\d{2}'
        self.quantity_pattern = r'(\d+)\s*@\s*\$?\d+\.\d{2}'
        self.date_patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        
        # Common keywords for different receipt formats
        self.total_keywords = [
            'total',
            'amount',
            'sum',
            'due',
            'payment',
            'balance'
        ]
        self.subtotal_keywords = [
            'subtotal',
            'sub-total',
            'sub total',
            'net amount'
        ]
        self.tax_keywords = [
            'tax',
            'vat',
            'gst',
            'hst',
            'sales tax'
        ]
        self.discount_keywords = [
            'discount',
            'savings',
            'off',
            'reduced',
            'coupon'
        ]

    def extract_text(self, image) -> str:
        """Extract text from preprocessed image using pytesseract."""
        return pytesseract.image_to_string(image)

    def extract_receipt_data(self, text: str) -> Receipt:
        """Parse receipt text and extract structured data."""
        # Clean and normalize text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_lines = self._clean_text(lines)
        
        # Extract basic information
        store_name = self._extract_store_name(cleaned_lines)
        date = self._extract_date(text)
        
        # Extract items with quantities
        items = self._extract_items(cleaned_lines)
        
        # Extract financial details
        subtotal, tax, total = self._extract_totals(cleaned_lines)
        
        return Receipt(
            store_name=store_name,
            date=date,
            items=items,
            total=total,
            subtotal=subtotal,
            tax=tax,
            raw_text=text
        )

    def _clean_text(self, lines: List[str]) -> List[str]:
        """Clean and normalize text from receipt."""
        cleaned = []
        for line in lines:
            # Remove multiple spaces
            line = ' '.join(line.split())
            # Remove common noise characters
            line = re.sub(r'[*#]+', '', line)
            # Convert to uppercase for consistency
            line = line.upper()
            if line:
                cleaned.append(line)
        return cleaned

    def _extract_store_name(self, lines: List[str]) -> str:
        """Extract store name using various heuristics."""
        for i, line in enumerate(lines[:3]):  # Check first 3 lines
            # Skip lines that look like dates or times
            if any(re.search(pattern, line) for pattern in self.date_patterns):
                continue
            # Skip lines that are too long (usually not store names)
            if len(line) > 30:
                continue
            # Skip lines with prices
            if re.search(self.price_pattern, line):
                continue
            # Skip lines that are just numbers
            if re.match(r'^[\d\s]+$', line):
                continue
            return line.strip()
        return "Unknown Store"

    def _extract_date(self, text: str) -> datetime:
        """Extract date from receipt text."""
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    date_str = match.group()
                    # Try different date formats
                    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except ValueError:
                    continue
        return datetime.now()

    def _extract_items(self, lines: List[str]) -> List[ReceiptItem]:
        """Extract items and their prices from receipt."""
        items = []
        current_quantity = 1
        
        for line in lines:
            # Skip lines that look like totals or discounts
            if any(keyword in line.upper() for keyword in 
                  self.total_keywords + self.subtotal_keywords + 
                  self.tax_keywords + self.discount_keywords):
                continue

            # Check for quantity notation
            qty_match = re.search(self.quantity_pattern, line)
            if qty_match:
                current_quantity = int(qty_match.group(1))
            
            # Extract price
            price_match = re.search(self.price_pattern, line)
            if price_match:
                price_str = price_match.group()
                try:
                    price = float(price_str.replace('$', ''))
                    # Get description (everything before the price)
                    description = line[:price_match.start()].strip()
                    
                    # Clean up description
                    description = re.sub(r'\s+', ' ', description)
                    description = re.sub(r'^[\d\s]+', '', description)  # Remove leading numbers
                    
                    if description and not any(keyword in description.upper() 
                                            for keyword in self.total_keywords + 
                                            self.subtotal_keywords + 
                                            self.tax_keywords):
                        items.append(ReceiptItem(
                            description=description,
                            price=price,
                            quantity=current_quantity
                        ))
                    current_quantity = 1  # Reset quantity
                except ValueError:
                    continue
        
        return items

    def _extract_totals(self, lines: List[str]) -> Tuple[float, float, float]:
        """Extract subtotal, tax, and total amounts from receipt."""
        subtotal = 0.0
        tax = 0.0
        total = 0.0
        
        # Process lines in reverse (totals usually at bottom)
        for line in reversed(lines):
            line_upper = line.upper()
            
            # Extract total first
            if any(keyword in line_upper for keyword in self.total_keywords):
                if 'SUBTOTAL' not in line_upper:  # Skip subtotal lines
                    amount = self._extract_amount(line)
                    if amount > total:  # Take the largest total found
                        total = amount
            
            # Extract subtotal
            elif any(keyword in line_upper for keyword in self.subtotal_keywords):
                amount = self._extract_amount(line)
                if amount > subtotal:  # Take the largest subtotal found
                    subtotal = amount
            
            # Extract tax
            elif any(keyword in line_upper for keyword in self.tax_keywords):
                amount = self._extract_amount(line)
                tax += amount  # Sum up all tax amounts
        
        # If we couldn't find some values, try to calculate them
        if total == 0 and subtotal > 0 and tax > 0:
            total = subtotal + tax
        elif subtotal == 0 and total > 0 and tax > 0:
            subtotal = total - tax
        elif tax == 0 and total > 0 and subtotal > 0:
            tax = total - subtotal
        
        return subtotal, tax, total

    def _extract_amount(self, line: str) -> float:
        """Extract dollar amount from a line of text."""
        amounts = re.findall(r'\$?(\d+\.\d{2})', line)
        if amounts:
            try:
                # Return the last number in the line (usually the total)
                return float(amounts[-1])
            except ValueError:
                pass
        return 0.0