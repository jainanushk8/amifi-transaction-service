# @ai perplexity tf-lite-classifier
"""
Transaction classification with TensorFlow Lite interface.
Human decisions: Category mapping, confidence thresholds, TF-Lite integration pattern.
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.parsers import ParsedTransaction

@dataclass
class ClassificationResult:
    """Result of transaction classification."""
    category: str
    confidence: float
    subcategories: List[str]
    features_used: List[str]

class TFLiteInterface:
    """Interface for TensorFlow Lite model - ready for real model integration."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.is_model_loaded = False
        
        # Human decision: Standard fintech categories
        self.categories = [
            'shopping', 'utilities', 'food_dining', 'transportation',
            'entertainment', 'healthcare', 'education', 'bills',
            'transfer', 'investment', 'fee', 'cashback', 'other'
        ]
        
        if model_path:
            self._load_model()
        else:
            print("INFO: TF-Lite model not provided, using rule-based fallback")
    
    def _load_model(self):
        """Load TensorFlow Lite model - ready for real implementation."""
        try:
            # TODO: Implement actual TF-Lite loading
            # import tensorflow as tf
            # self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
            # self.interpreter.allocate_tensors()
            # self.input_details = self.interpreter.get_input_details()
            # self.output_details = self.interpreter.get_output_details()
            # self.is_model_loaded = True
            print(f"TODO: Load TF-Lite model from {self.model_path}")
        except Exception as e:
            print(f"WARNING: Could not load TF-Lite model: {e}")
            self.is_model_loaded = False
    
    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """Predict using TF-Lite model or fallback."""
        if self.is_model_loaded and self.model:
            return self._tflite_predict(features)
        else:
            return self._rule_based_predict(features)
    
    def _tflite_predict(self, features: np.ndarray) -> Tuple[str, float]:
        """Real TF-Lite prediction - ready for implementation."""
        # TODO: Implement actual TF-Lite inference
        # self.interpreter.set_tensor(self.input_details[0]['index'], features)
        # self.interpreter.invoke()
        # output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        # predicted_class = np.argmax(output_data)
        # confidence = float(np.max(output_data))
        # return self.categories[predicted_class], confidence
        
        # Placeholder for now
        return "other", 0.5
    
    def _rule_based_predict(self, features: Dict) -> Tuple[str, float]:
        """Rule-based classification as TF-Lite fallback."""
        merchant = features.get('merchant', '').lower()
        txn_type = features.get('transaction_type', '').lower()
        amount = features.get('amount', 0)
        
        # Human decision: Business logic for classification
        
        # Shopping patterns
        if any(store in merchant for store in ['amazon', 'flipkart', 'myntra', 'mall']):
            return 'shopping', 0.9
        
        # Utilities
        if any(util in merchant for util in ['mseb', 'electricity', 'gas', 'water']):
            return 'utilities', 0.95
        
        # Entertainment
        if any(ent in merchant for ent in ['netflix', 'spotify', 'prime', 'cinema']):
            return 'entertainment', 0.9
        
        # Bills based on transaction type
        if txn_type == 'bill':
            return 'bills', 0.85
        
        # UPI/NEFT transfers
        if 'upi' in features.get('raw_message', '').lower() or 'neft' in features.get('raw_message', '').lower():
            return 'transfer', 0.8
        
        # Credit card fees (small amounts on credit cards)
        if amount < 100 and 'credit card' in features.get('raw_message', '').lower():
            return 'fee', 0.75
        
        # Interest credits
        if txn_type == 'credit' and 'interest' in features.get('raw_message', '').lower():
            return 'cashback', 0.9
        
        # Default fallback
        return 'other', 0.3

class TransactionClassifier:
    """Main transaction classification service."""
    
    def __init__(self, tflite_model_path: Optional[str] = None):
        self.tflite_interface = TFLiteInterface(tflite_model_path)
        
        # Human decision: Feature extraction strategy
        self.feature_extractors = {
            'merchant_keywords': self._extract_merchant_features,
            'amount_patterns': self._extract_amount_features,
            'time_patterns': self._extract_time_features,
            'channel_info': self._extract_channel_features
        }
    
    def classify_transaction(self, transaction: ParsedTransaction) -> ClassificationResult:
        """Classify a parsed transaction."""
        
        # Extract features for classification
        features = self._extract_features(transaction)
        
        # Get prediction from TF-Lite interface
        category, confidence = self.tflite_interface.predict(features)
        
        # Generate subcategories based on rules
        subcategories = self._generate_subcategories(transaction, category)
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            subcategories=subcategories,
            features_used=list(features.keys())
        )
    
    def _extract_features(self, transaction: ParsedTransaction) -> Dict:
        """Extract features for classification."""
        features = {
            'amount': transaction.amount,
            'transaction_type': transaction.transaction_type,
            'merchant': transaction.merchant or '',
            'channel': transaction.channel,
            'raw_message': transaction.raw_message,
            'has_account_ref': transaction.account_ref is not None,
            'has_reference': transaction.reference is not None,
        }
        
        # Add computed features
        for name, extractor in self.feature_extractors.items():
            features.update(extractor(transaction))
        
        return features
    
    def _extract_merchant_features(self, transaction: ParsedTransaction) -> Dict:
        """Extract merchant-based features."""
        merchant = (transaction.merchant or '').lower()
        
        return {
            'is_ecommerce': any(store in merchant for store in ['amazon', 'flipkart', 'myntra']),
            'is_streaming': any(stream in merchant for stream in ['netflix', 'spotify', 'prime']),
            'is_utility': any(util in merchant for util in ['mseb', 'electricity', 'gas']),
        }
    
    def _extract_amount_features(self, transaction: ParsedTransaction) -> Dict:
        """Extract amount-based features."""
        amount = transaction.amount
        
        return {
            'is_micro_transaction': amount < 10,
            'is_small_transaction': 10 <= amount < 500,
            'is_medium_transaction': 500 <= amount < 5000,
            'is_large_transaction': amount >= 5000,
            'amount_bucket': self._get_amount_bucket(amount)
        }
    
    def _extract_time_features(self, transaction: ParsedTransaction) -> Dict:
        """Extract time-based features."""
        hour = transaction.timestamp.hour
        weekday = transaction.timestamp.weekday()
        
        return {
            'is_business_hours': 9 <= hour <= 17,
            'is_weekend': weekday >= 5,
            'time_bucket': self._get_time_bucket(hour)
        }
    
    def _extract_channel_features(self, transaction: ParsedTransaction) -> Dict:
        """Extract channel-based features."""
        return {
            'is_sms': transaction.channel == 'sms',
            'is_email': transaction.channel == 'email',
            'message_length': len(transaction.raw_message)
        }
    
    def _get_amount_bucket(self, amount: float) -> str:
        """Categorize amount into buckets."""
        if amount < 100:
            return 'micro'
        elif amount < 1000:
            return 'small'
        elif amount < 5000:
            return 'medium'
        else:
            return 'large'
    
    def _get_time_bucket(self, hour: int) -> str:
        """Categorize time into buckets."""
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _generate_subcategories(self, transaction: ParsedTransaction, primary_category: str) -> List[str]:
        """Generate relevant subcategories."""
        subcategories = []
        
        # Human decision: Subcategory logic
        if primary_category == 'shopping':
            if transaction.amount > 2000:
                subcategories.append('high_value_purchase')
            if 'amazon' in (transaction.merchant or '').lower():
                subcategories.append('online_marketplace')
        
        elif primary_category == 'utilities':
            if transaction.amount > 1000:
                subcategories.append('high_utility_bill')
        
        elif primary_category == 'bills':
            subcategories.append('recurring_payment')
            if 'due' in transaction.raw_message.lower():
                subcategories.append('payment_reminder')
        
        return subcategories

# Export for easy imports
__all__ = ['TransactionClassifier', 'ClassificationResult', 'TFLiteInterface']
