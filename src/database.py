# @ai perplexity database-models
"""
Database models and connection management for AmiFi transaction service.
Human decisions: Schema design, relationship mapping, idempotency strategy.
"""

import sqlite3
import uuid
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

class DatabaseManager:
    """Handles all database operations with proper error handling."""
    
    def __init__(self, db_path: str = "amifi_transactions.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema if not exists."""
        schema_path = Path("schema.sql")
        if not schema_path.exists():
            raise FileNotFoundError("schema.sql not found")
            
        with sqlite3.connect(self.db_path) as conn:
            with open("schema.sql", 'r') as schema_file:
                conn.executescript(schema_file.read())
    
    def get_connection(self):
        """Get database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def generate_transaction_hash(self, raw_message: str) -> str:
        """Generate idempotency hash for transaction."""
        # Human decision: Use SHA-256 for reliable deduplication
        return hashlib.sha256(raw_message.encode('utf-8')).hexdigest()
    
    def upsert_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Insert or update transaction with idempotency."""
        transaction_id = str(uuid.uuid4())
        transaction_hash = self.generate_transaction_hash(transaction_data['raw_message'])
        
        with self.get_connection() as conn:
            # Check if transaction already exists
            existing = conn.execute(
                "SELECT id FROM transactions WHERE hash = ?", 
                (transaction_hash,)
            ).fetchone()
            
            if existing:
                return existing['id']  # Return existing ID
            
            # Insert new transaction
            conn.execute("""
                INSERT INTO transactions (
                    id, userid, ts, amount, currency, account_ref, 
                    channel, raw_msg_id, hash, type, category, 
                    confidence, meta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                transaction_data.get('userid', 'demo-user'),
                transaction_data['timestamp'],
                transaction_data['amount'],
                transaction_data.get('currency', 'INR'),
                transaction_data.get('account_ref'),
                transaction_data['channel'],
                transaction_hash,  # raw_msg_id = hash for simplicity
                transaction_hash,
                transaction_data['type'],
                transaction_data.get('category'),
                transaction_data.get('confidence', 0.0),
                json.dumps(transaction_data.get('meta', {}))
            ))
            
            return transaction_id
    
    def add_goal_impact(self, transaction_id: str, goal_id: str, 
                       impact_score: float, message: str) -> str:
        """Add goal impact entry."""
        impact_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO goal_impacts (id, transaction_id, goal_id, impact_score, message)
                VALUES (?, ?, ?, ?, ?)
            """, (impact_id, transaction_id, goal_id, impact_score, message))
            
        return impact_id
    
    def get_transactions(self, limit: int = 100) -> list:
        """Get recent transactions."""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM transactions 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_transaction_with_impacts(self, transaction_id: str) -> Optional[Dict]:
        """Get transaction with associated goal impacts."""
        with self.get_connection() as conn:
            transaction = conn.execute("""
                SELECT * FROM transactions WHERE id = ?
            """, (transaction_id,)).fetchone()
            
            if not transaction:
                return None
            
            impacts = conn.execute("""
                SELECT * FROM goal_impacts WHERE transaction_id = ?
            """, (transaction_id,)).fetchall()
            
            result = dict(transaction)
            result['goal_impacts'] = [dict(impact) for impact in impacts]
            
            return result
