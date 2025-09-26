# @ai perplexity sms-email-parsers
"""
SMS and Email transaction parsers for AmiFi.
Human decisions: Regex patterns, field mapping, confidence scoring.
"""

import re
import hashlib
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

@dataclass
class ParsedTransaction:
    """Structured transaction data from parsing."""
    amount: float
    currency: str
    transaction_type: str  # credit, debit, bill, fee, other
    timestamp: datetime
    account_ref: Optional[str]
    merchant: Optional[str]
    reference: Optional[str]
    confidence: float
    raw_message: str
    channel: str  # sms or email
    meta: Dict[str, Any]

class SMSParser:
    """Parse SMS transaction messages using regex patterns."""
    
    def __init__(self):
        # Human decision: Common Indian bank SMS patterns
        self.patterns = [
            # HDFC Credit Card spending
            {
                'regex': r'INR ([\d,]+\.?\d*) spent on.*?(\w+ Credit Card) (XX\d+) at (.*?) on (\d{2}-\d{2}-\d{4}) (\d{4})',
                'type': 'debit',
                'confidence': 0.95,
                'fields': ['amount', 'account_type', 'account_ref', 'merchant', 'date', 'time']
            },
            # NEFT Credit 
            {
                'regex': r'INR ([\d,]+\.?\d*) credited to AC (\d+) (\w+) via NEFT on (\d{2}-\d{2}-\d{4}) (\d{4})\. Ref ([A-Z0-9]+)',
                'type': 'credit', 
                'confidence': 0.95,
                'fields': ['amount', 'account_ref', 'bank', 'date', 'time', 'reference']
            },
            # UPI Payment
            {
                'regex': r'INR ([\d,]+\.?\d*) paid to (.*?) via UPI Ref ([A-Z0-9]+) on (\d{2}-\d{2}-\d{4}) (\d{4})',
                'type': 'debit',
                'confidence': 0.90,
                'fields': ['amount', 'merchant', 'reference', 'date', 'time']
            },
            # Bill Payment Reminder
            {
                'regex': r'Reminder.*?payment of INR ([\d,]+) due on (\d{2}-\d{2}-\d{4}) for (\w+) (XX\d+)',
                'type': 'bill',
                'confidence': 0.85,
                'fields': ['amount', 'due_date', 'bank', 'account_ref']
            }
        ]
    
    def parse_message(self, sms_text: str) -> Optional[ParsedTransaction]:
        """Parse single SMS message."""
        sms_text = sms_text.strip()
        
        for pattern_info in self.patterns:
            match = re.search(pattern_info['regex'], sms_text, re.IGNORECASE)
            if match:
                return self._extract_transaction_data(
                    match, pattern_info, sms_text
                )
        
        # Generic fallback for unmatched messages
        amount_match = re.search(r'INR ([\d,]+\.?\d*)', sms_text)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            return ParsedTransaction(
                amount=float(amount_str),
                currency='INR',
                transaction_type='other',
                timestamp=datetime.now(),  # Fallback timestamp
                account_ref=None,
                merchant=None,
                reference=None,
                confidence=0.3,  # Low confidence for generic parse
                raw_message=sms_text,
                channel='sms',
                meta={'parser': 'generic_fallback'}
            )
        
        return None
    
    def _extract_transaction_data(self, match, pattern_info, raw_message):
        """Extract structured data from regex match."""
        groups = match.groups()
        fields = pattern_info['fields']
        
        # Parse amount (always first field)
        amount_str = groups[0].replace(',', '')
        amount = float(amount_str)
        
        # Parse timestamp
        timestamp = self._parse_timestamp(groups, fields)
        
        # Extract other fields
        account_ref = self._extract_field(groups, fields, ['account_ref'])
        merchant = self._extract_field(groups, fields, ['merchant'])
        reference = self._extract_field(groups, fields, ['reference'])
        
        return ParsedTransaction(
            amount=amount,
            currency='INR',
            transaction_type=pattern_info['type'],
            timestamp=timestamp,
            account_ref=account_ref,
            merchant=merchant,
            reference=reference,
            confidence=pattern_info['confidence'],
            raw_message=raw_message,
            channel='sms',
            meta={
                'parser': 'regex_pattern',
                'pattern_matched': pattern_info['fields']
            }
        )
    
    def _parse_timestamp(self, groups, fields):
        """Parse timestamp from matched groups."""
        date_idx = next((i for i, f in enumerate(fields) if 'date' in f), None)
        time_idx = next((i for i, f in enumerate(fields) if 'time' in f), None)
        
        if date_idx is not None and time_idx is not None:
            date_str = groups[date_idx]  # DD-MM-YYYY
            time_str = groups[time_idx]  # HHMM
            
            try:
                # Parse date
                day, month, year = date_str.split('-')
                # Parse time
                hour = int(time_str[:2])
                minute = int(time_str[2:])
                
                return datetime(int(year), int(month), int(day), hour, minute)
            except (ValueError, IndexError):
                pass
        
        # Fallback to current time
        return datetime.now()
    
    def _extract_field(self, groups, fields, target_fields):
        """Extract specific field from groups."""
        for target in target_fields:
            try:
                idx = fields.index(target)
                if idx < len(groups):
                    return groups[idx]
            except ValueError:
                continue
        return None

class EmailParser:
    """Parse email transaction messages."""
    
    def __init__(self):
        # Human decision: Email-specific patterns
        self.patterns = [
            # Interest credit
            {
                'regex': r'interest INR ([\d,]+\.?\d*) has been credited on (\d+ \w+)',
                'type': 'credit',
                'confidence': 0.90,
                'fields': ['amount', 'date']
            },
            # Bill payment
            {
                'regex': r'INR ([\d,]+\.?\d*) paid to (\w+)\. Txn ([A-Z0-9]+) on (\d+ \w+ \d+)',
                'type': 'debit', 
                'confidence': 0.85,
                'fields': ['amount', 'merchant', 'reference', 'date']
            }
        ]
    
    def parse_message(self, email_text: str) -> Optional[ParsedTransaction]:
        """Parse email message."""
        email_text = email_text.strip()
        
        for pattern_info in self.patterns:
            match = re.search(pattern_info['regex'], email_text, re.IGNORECASE)
            if match:
                return self._extract_email_transaction(
                    match, pattern_info, email_text
                )
        
        return None
    
    def _extract_email_transaction(self, match, pattern_info, raw_message):
        """Extract transaction from email match."""
        groups = match.groups()
        amount_str = groups[0].replace(',', '')
        
        return ParsedTransaction(
            amount=float(amount_str),
            currency='INR',
            transaction_type=pattern_info['type'],
            timestamp=datetime.now(),  # Simplified for now
            account_ref=None,
            merchant=groups[1] if len(groups) > 1 else None,
            reference=groups[2] if len(groups) > 2 else None,
            confidence=pattern_info['confidence'],
            raw_message=raw_message,
            channel='email',
            meta={'parser': 'email_regex'}
        )

class TransactionParser:
    """Main parser coordinator."""
    
    def __init__(self):
        self.sms_parser = SMSParser()
        self.email_parser = EmailParser()
    
    def parse_sms_file(self, filepath: str) -> List[ParsedTransaction]:
        """Parse SMS file and return transactions."""
        transactions = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                parsed = self.sms_parser.parse_message(line)
                if parsed:
                    # Add line number to meta for debugging
                    parsed.meta['line_number'] = line_num
                    transactions.append(parsed)
        
        return transactions
    
    def parse_email_file(self, filepath: str) -> List[ParsedTransaction]:
        """Parse email file and return transactions."""
        transactions = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                parsed = self.email_parser.parse_message(line)
                if parsed:
                    parsed.meta['line_number'] = line_num
                    transactions.append(parsed)
        
        return transactions
