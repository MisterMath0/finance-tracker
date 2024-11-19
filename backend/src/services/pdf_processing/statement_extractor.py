# backend/src/services/pdf_processing/statement_extractor.py
import pdfplumber
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Tuple
import re
from rich.console import Console
from rich.table import Table

console = Console()

@dataclass
class BankTransaction:
    date: datetime
    description: str
    amount: float
    transaction_type: str  # 'debit' or 'credit'
    category: Optional[str] = None
    raw_text: str = ""

class StatementProcessor:
    def __init__(self):
        # Enhanced date patterns
        self.date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # 01/23/2024, 01-23-24
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # 2024/01/23
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}',  # January 23, 2024
            r'\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}'     # 23 January 2024
        ]
        
        # Enhanced amount patterns
        self.amount_patterns = [
            r'\$?\d{1,3}(?:,\d{3})*\.\d{2}',     # $1,234.56 or 1,234.56
            r'\$?\d+\.\d{2}',                     # $123.45 or 123.45
            r'-\$?\d{1,3}(?:,\d{3})*\.\d{2}',    # -$1,234.56
            r'-\$?\d+\.\d{2}'                     # -$123.45
        ]
        
        # Transaction markers
        self.transaction_markers = [
            r'(balance|payment|deposit|withdrawal|transfer|pos|debit|credit|check|#\d+)',
            r'\d{4}',  # Last 4 digits of card/account
            r'\$'      # Dollar sign
        ]

    async def process_statement(self, pdf_path: str, openai_api_key: str) -> List[BankTransaction]:
        """Process a bank statement PDF and return categorized transactions."""
        try:
            console.print("\n[bold yellow]Opening PDF file...[/]")
            with pdfplumber.open(pdf_path) as pdf:
                console.print(f"Successfully opened PDF with {len(pdf.pages)} pages")
                
                # Extract tables and text from each page
                transactions = []
                for i, page in enumerate(pdf.pages):
                    console.print(f"\n[bold blue]Processing page {i+1}...[/]")
                    
                    # Try to extract tables first
                    tables = page.extract_tables()
                    if tables:
                        console.print(f"Found {len(tables)} tables on page {i+1}")
                        transactions.extend(self._process_tables(tables))
                    
                    # Extract and process text
                    text = page.extract_text()
                    text_transactions = self._process_text(text)
                    transactions.extend(text_transactions)
                    
                    console.print(f"Found {len(text_transactions)} transactions in text on page {i+1}")
                    
                    # Debug output
                    if not tables and not text_transactions:
                        console.print("[yellow]No transactions found on this page. Sample text:[/]")
                        lines = text.split('\n')[:5]
                        for line in lines:
                            console.print(f"LINE: {line}")
                
                return transactions
                
        except Exception as e:
            console.print(f"[bold red]Error processing PDF: {str(e)}[/]")
            raise

    def _process_tables(self, tables: List[List[List[str]]]) -> List[BankTransaction]:
        """Process extracted tables from the PDF."""
        transactions = []
        
        for table in tables:
            # Skip empty tables
            if not table or not any(table):
                continue
                
            console.print("\n[yellow]Processing table:[/]")
            self._debug_print_table(table)
            
            # Try to identify header row and column positions
            date_col, desc_col, amount_col = self._identify_columns(table)
            
            if date_col is not None:
                # Process each row
                for row in table[1:]:  # Skip header row
                    if len(row) > max(date_col, desc_col, amount_col):
                        try:
                            date_str = str(row[date_col]).strip()
                            date = self._parse_date(date_str)
                            
                            if date:
                                description = str(row[desc_col]).strip()
                                amount_str = str(row[amount_col]).strip()
                                
                                # Try to extract amount
                                amount = self._extract_amount(amount_str)
                                if amount:
                                    transaction = BankTransaction(
                                        date=date,
                                        description=description,
                                        amount=abs(amount),
                                        transaction_type='debit' if amount < 0 else 'credit',
                                        raw_text=' '.join(str(x) for x in row if x)
                                    )
                                    transactions.append(transaction)
                                    console.print(f"[green]Found transaction: {description} - ${abs(amount):.2f}[/]")
                        
                        except Exception as e:
                            console.print(f"[red]Error processing row: {str(e)}[/]")
                            continue
        
        return transactions

    def _process_text(self, text: str) -> List[BankTransaction]:
        """Process raw text to extract transactions."""
        transactions = []
        lines = text.split('\n')
        
        # Group lines that might belong to the same transaction
        transaction_groups = self._group_transaction_lines(lines)
        
        for group in transaction_groups:
            combined_text = ' '.join(group)
            
            # Try to extract transaction components
            date = self._find_date(combined_text)
            if not date:
                continue
                
            amounts = self._find_amounts(combined_text)
            if not amounts:
                continue
                
            # Use the last amount found as the transaction amount
            amount = amounts[-1]
            
            # Clean description by removing date and amount
            description = self._clean_description(combined_text, amounts)
            
            if date and amount and description:
                transaction = BankTransaction(
                    date=date,
                    description=description,
                    amount=abs(amount),
                    transaction_type='debit' if amount < 0 else 'credit',
                    raw_text=combined_text
                )
                transactions.append(transaction)
                console.print(f"[green]Found transaction: {description} - ${abs(amount):.2f}[/]")
        
        return transactions

    def _identify_columns(self, table: List[List[str]]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Identify the positions of date, description, and amount columns."""
        if not table or not table[0]:
            return None, None, None
            
        header = [str(cell).lower() for cell in table[0]]
        
        date_col = self._find_column_index(header, ['date', 'time', 'posted'])
        desc_col = self._find_column_index(header, ['description', 'details', 'transaction', 'particulars'])
        amount_col = self._find_column_index(header, ['amount', 'sum', 'debit', 'credit', 'payment'])
        
        if date_col is None or desc_col is None or amount_col is None:
            # Try to identify columns by content if headers not found
            for i, row in enumerate(table[1:3]):  # Check first few rows
                for j, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    if date_col is None and self._find_date(cell_str):
                        date_col = j
                    if amount_col is None and self._find_amounts(cell_str):
                        amount_col = j
            
            # If we found date and amount, assume description is in between
            if date_col is not None and amount_col is not None:
                middle_cols = list(range(min(date_col, amount_col) + 1, max(date_col, amount_col)))
                if middle_cols:
                    desc_col = middle_cols[0]
        
        return date_col, desc_col, amount_col

    def _group_transaction_lines(self, lines: List[str]) -> List[List[str]]:
        """Group lines that might belong to the same transaction."""
        groups = []
        current_group = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Start new group if we find a date
            if self._find_date(line):
                if current_group:
                    groups.append(current_group)
                current_group = [line]
            else:
                # Add to current group if it might be part of the transaction
                if current_group and (
                    self._find_amounts(line) or
                    any(re.search(pattern, line.lower()) for pattern in self.transaction_markers)
                ):
                    current_group.append(line)
                elif current_group:
                    groups.append(current_group)
                    current_group = []
        
        if current_group:
            groups.append(current_group)
        
        return groups

    def _find_column_index(self, header: List[str], possible_names: List[str]) -> Optional[int]:
        """Find the index of a column in the header."""
        for name in possible_names:
            for i, cell in enumerate(header):
                if name in cell.lower():
                    return i
        return None

    def _clean_description(self, text: str, amounts: List[float]) -> str:
        """Clean transaction description."""
        # Remove dates
        for pattern in self.date_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove amounts
        for amount in amounts:
            text = text.replace(f"${abs(amount):.2f}", '')
            text = text.replace(f"-${abs(amount):.2f}", '')
            text = text.replace(f"${abs(amount):,.2f}", '')
            text = text.replace(f"-${abs(amount):,.2f}", '')
        
        # Clean up extra spaces and special characters
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'^\W+|\W+$', '', text)
        
        return text.strip()

    def _debug_print_table(self, table: List[List[str]]):
        """Print table contents for debugging."""
        if not table:
            return
            
        debug_table = Table(show_header=True)
        for i in range(max(len(row) for row in table)):
            debug_table.add_column(f"Col {i}")
            
        for row in table[:5]:  # Show first 5 rows
            debug_table.add_row(*[str(cell) for cell in row + [''] * (len(debug_table.columns) - len(row))])
            
        console.print(debug_table)

    def _find_date(self, text: str) -> Optional[datetime]:
        """Extract date from text."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group()
                    # Try different date formats
                    for fmt in [
                        '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%y',
                        '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y'
                    ]:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None

    def _find_amounts(self, text: str) -> List[float]:
        """Extract all amounts from text."""
        amounts = []
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Remove currency symbols and commas
                    clean_amount = match.replace('$', '').replace(',', '')
                    amount = float(clean_amount)
                    amounts.append(amount)
                except ValueError:
                    continue
        return amounts

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract single amount from text."""
        amounts = self._find_amounts(text)
        return amounts[-1] if amounts else None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object."""
        return self._find_date(date_str)