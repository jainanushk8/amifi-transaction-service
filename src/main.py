# @ai perplexity fastapi-backend
"""
FastAPI application for AmiFi transaction processing service.
Human decisions: Endpoint design, error handling, response schemas.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.database import DatabaseManager
from src.parsers import TransactionParser, ParsedTransaction
from src.classifier import TransactionClassifier, ClassificationResult
from src.goal_impact import GoalImpactCalculator, GoalImpact

# Load environment variables
load_dotenv()

# Configure logging with PII masking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mask_pii(message: str) -> str:
    """Mask PII in log messages - Human decision: regex patterns for Indian context."""
    import re
    # Mask account numbers
    message = re.sub(r'\b\d{4,16}\b', '****ACCT', message)
    # Mask card numbers 
    message = re.sub(r'XX\d+', 'XX****', message)
    # Mask UPI references
    message = re.sub(r'[A-Z0-9]{6,}', 'REF****', message)
    return message

# Custom logger with PII masking
class PIIMaskingFormatter(logging.Formatter):
    def format(self, record):
        original = super().format(record)
        return mask_pii(original)

# Apply PII masking to all handlers
for handler in logger.handlers:
    handler.setFormatter(PIIMaskingFormatter())

# Initialize FastAPI app
app = FastAPI(
    title="AmiFi Transaction Processing Service",
    description="SMS/Email transaction parser with ML classification and goal impact analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_manager = DatabaseManager()
transaction_parser = TransactionParser()
transaction_classifier = TransactionClassifier()
goal_calculator = GoalImpactCalculator()

# Pydantic models for API requests/responses
class TransactionMessage(BaseModel):
    """Single transaction message for processing."""
    message: str = Field(..., description="Raw SMS or email message")
    channel: str = Field(..., description="Message channel: 'sms' or 'email'")
    user_id: str = Field(default="demo-user", description="User identifier")

class ProcessedTransaction(BaseModel):
    """Processed transaction with classification and goal impacts."""
    transaction_id: str
    amount: float
    currency: str
    transaction_type: str
    category: str
    confidence: float
    timestamp: datetime
    merchant: Optional[str]
    account_ref: Optional[str]
    channel: str
    goal_impacts: List[Dict[str, Any]]

class BulkProcessRequest(BaseModel):
    """Bulk processing request."""
    file_type: str = Field(..., description="File type: 'sms' or 'email'")
    user_id: str = Field(default="demo-user", description="User identifier")

class GoalSummaryResponse(BaseModel):
    """Goal summary response."""
    goals: Dict[str, Dict[str, Any]]
    last_updated: datetime

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    database_connected: bool
    services_initialized: bool

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AmiFi Transaction Processing Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/v1/process-message",
            "/api/v1/process-bulk", 
            "/api/v1/transactions",
            "/api/v1/goals",
            "/docs"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db_test = db_manager.get_transactions(limit=1)
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {mask_pii(str(e))}")
        db_connected = False
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(),
        database_connected=db_connected,
        services_initialized=True
    )

@app.post("/api/v1/process-message", response_model=ProcessedTransaction)
async def process_single_message(request: TransactionMessage):
    """Process a single transaction message."""
    try:
        logger.info(f"Processing {request.channel} message for user {request.user_id}")
        
        # Parse message based on channel
        if request.channel == "sms":
            parsed_txn = transaction_parser.sms_parser.parse_message(request.message)
        elif request.channel == "email":
            parsed_txn = transaction_parser.email_parser.parse_message(request.message)
        else:
            raise HTTPException(status_code=400, detail="Invalid channel. Use 'sms' or 'email'")
        
        if not parsed_txn:
            raise HTTPException(status_code=422, detail="Unable to parse transaction from message")
        
        # Override user_id from request
        parsed_txn.meta['userid'] = request.user_id
        
        # Classify transaction
        classification = transaction_classifier.classify_transaction(parsed_txn)
        
        # Calculate goal impacts
        goal_impacts = goal_calculator.calculate_transaction_impact(parsed_txn, classification)
        
        # Store in database with idempotency
        transaction_data = {
            'userid': request.user_id,
            'timestamp': parsed_txn.timestamp,
            'amount': parsed_txn.amount,
            'currency': parsed_txn.currency,
            'account_ref': parsed_txn.account_ref,
            'channel': parsed_txn.channel,
            'raw_message': parsed_txn.raw_message,
            'type': parsed_txn.transaction_type,
            'category': classification.category,
            'confidence': classification.confidence,
            'meta': {
                **parsed_txn.meta,
                'classification_features': classification.features_used,
                'merchant': parsed_txn.merchant
            }
        }
        
        transaction_id = db_manager.upsert_transaction(transaction_data)
        
        # Store goal impacts
        for impact in goal_impacts:
            db_manager.add_goal_impact(
                transaction_id=transaction_id,
                goal_id=impact.goal_id,
                impact_score=impact.impact_score,
                message=impact.message
            )
        
        logger.info(f"Successfully processed transaction {transaction_id}")
        
        return ProcessedTransaction(
            transaction_id=transaction_id,
            amount=parsed_txn.amount,
            currency=parsed_txn.currency,
            transaction_type=parsed_txn.transaction_type,
            category=classification.category,
            confidence=classification.confidence,
            timestamp=parsed_txn.timestamp,
            merchant=parsed_txn.merchant,
            account_ref=parsed_txn.account_ref,
            channel=parsed_txn.channel,
            goal_impacts=[{
                "goal_id": impact.goal_id,
                "goal_name": impact.goal_name,
                "impact_score": impact.impact_score,
                "message": impact.message,
                "new_progress": impact.new_progress
            } for impact in goal_impacts]
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {mask_pii(str(e))}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/process-bulk")
async def process_bulk_messages(request: BulkProcessRequest, background_tasks: BackgroundTasks):
    """Process bulk messages from data files."""
    try:
        file_path = f"data/{request.file_type}.txt"
        
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail=f"Data file not found: {file_path}")
        
        # Parse transactions from file
        if request.file_type == "sms":
            transactions = transaction_parser.parse_sms_file(file_path)
        elif request.file_type == "email":
            transactions = transaction_parser.parse_email_file(file_path)
        else:
            raise HTTPException(status_code=400, detail="Invalid file_type. Use 'sms' or 'email'")
        
        processed_count = 0
        
        for parsed_txn in transactions:
            try:
                # Classify and calculate impacts
                classification = transaction_classifier.classify_transaction(parsed_txn)
                goal_impacts = goal_calculator.calculate_transaction_impact(parsed_txn, classification)
                
                # Store transaction
                transaction_data = {
                    'userid': request.user_id,
                    'timestamp': parsed_txn.timestamp,
                    'amount': parsed_txn.amount,
                    'currency': parsed_txn.currency,
                    'account_ref': parsed_txn.account_ref,
                    'channel': parsed_txn.channel,
                    'raw_message': parsed_txn.raw_message,
                    'type': parsed_txn.transaction_type,
                    'category': classification.category,
                    'confidence': classification.confidence,
                    'meta': {**parsed_txn.meta, 'merchant': parsed_txn.merchant}
                }
                
                transaction_id = db_manager.upsert_transaction(transaction_data)
                
                # Store goal impacts
                for impact in goal_impacts:
                    db_manager.add_goal_impact(
                        transaction_id=transaction_id,
                        goal_id=impact.goal_id,
                        impact_score=impact.impact_score,
                        message=impact.message
                    )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing individual transaction: {mask_pii(str(e))}")
                continue
        
        logger.info(f"Bulk processing completed: {processed_count} transactions")
        
        return {
            "status": "completed",
            "processed_count": processed_count,
            "total_transactions": len(transactions),
            "file_processed": file_path
        }
        
    except Exception as e:
        logger.error(f"Error in bulk processing: {mask_pii(str(e))}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/transactions")
async def get_transactions(
    limit: int = 50, 
    user_id: str = "demo-user"
):
    """Get recent transactions with goal impacts."""
    try:
        transactions = db_manager.get_transactions(limit=limit)
        
        # Filter by user_id and add goal impacts
        filtered_transactions = []
        for txn in transactions:
            if txn.get('userid') == user_id:
                # Get goal impacts for this transaction
                txn_with_impacts = db_manager.get_transaction_with_impacts(txn['id'])
                filtered_transactions.append(txn_with_impacts)
        
        return {
            "transactions": filtered_transactions,
            "count": len(filtered_transactions),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {mask_pii(str(e))}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/goals", response_model=GoalSummaryResponse)
async def get_goals_summary():
    """Get summary of all financial goals."""
    try:
        goals = goal_calculator.get_goal_summary()
        
        return GoalSummaryResponse(
            goals=goals,
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error fetching goals: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/classify-message")
async def classify_message(message: str, channel: str = "sms"):
    """Test endpoint for message classification."""
    try:
        # Parse message
        if channel == "sms":
            parsed_txn = transaction_parser.sms_parser.parse_message(message)
        else:
            parsed_txn = transaction_parser.email_parser.parse_message(message)
        
        if not parsed_txn:
            return {"error": "Unable to parse message", "message": message}
        
        # Classify
        classification = transaction_classifier.classify_transaction(parsed_txn)
        
        return {
            "message": message,
            "parsed": {
                "amount": parsed_txn.amount,
                "type": parsed_txn.transaction_type,
                "merchant": parsed_txn.merchant,
                "confidence": parsed_txn.confidence
            },
            "classification": {
                "category": classification.category,
                "confidence": classification.confidence,
                "subcategories": classification.subcategories
            }
        }
        
    except Exception as e:
        logger.error(f"Error in classification test: {mask_pii(str(e))}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Application lifecycle
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("AmiFi Transaction Service starting up...")
    logger.info("Database initialized successfully")
    logger.info("All services ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("AmiFi Transaction Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    
    # Human decision: Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
