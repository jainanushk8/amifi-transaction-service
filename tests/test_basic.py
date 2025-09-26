# @ai perplexity unit-tests
"""
Basic unit tests for AmiFi Transaction Service.
Human decisions: Test cases, assertion logic, mock scenarios.
"""

import pytest
from datetime import datetime
from src.parsers import TransactionParser
from src.classifier import TransactionClassifier
from src.goal_impact import GoalImpactCalculator

class TestTransactionParsing:
    """Test transaction parsing functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.parser = TransactionParser()
    
    def test_sms_parsing_amazon_transaction(self):
        """Test parsing of Amazon credit card transaction."""
        sms_text = "INR 1,249.00 spent on HDFC Credit Card XX1234 at AMAZON on 23-09-2025 1435. Avl Lmt INR 45,670."
        
        result = self.parser.sms_parser.parse_message(sms_text)
        
        assert result is not None
        assert result.amount == 1249.0
        assert result.merchant == "AMAZON"
        assert result.transaction_type == "debit"
        assert result.currency == "INR"
        assert result.confidence >= 0.9
    
    def test_sms_parsing_neft_credit(self):
        """Test parsing of NEFT credit transaction."""
        sms_text = "INR 4,999.00 credited to AC 9876 ICICI via NEFT on 23-09-2025 1805. Ref ABCD123."
        
        result = self.parser.sms_parser.parse_message(sms_text)
        
        assert result is not None
        assert result.amount == 4999.0
        assert result.transaction_type == "credit"
        assert result.account_ref == "9876"
        assert result.reference == "ABCD123"
    
    def test_email_parsing_interest_credit(self):
        """Test parsing of email interest credit."""
        email_text = "Subject: Statement Ready - Kotak Savings Body: Dear Customer, your monthly interest INR 210.00 has been credited on 30 Sep."
        
        result = self.parser.email_parser.parse_message(email_text)
        
        assert result is not None
        assert result.amount == 210.0
        assert result.transaction_type == "credit"

class TestTransactionClassification:
    """Test transaction classification functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = TransactionClassifier()
        self.parser = TransactionParser()
    
    def test_amazon_shopping_classification(self):
        """Test classification of Amazon transaction as shopping."""
        sms_text = "INR 1,249.00 spent on HDFC Credit Card XX1234 at AMAZON on 23-09-2025 1435. Avl Lmt INR 45,670."
        parsed = self.parser.sms_parser.parse_message(sms_text)
        
        classification = self.classifier.classify_transaction(parsed)
        
        assert classification.category == "shopping"
        assert classification.confidence >= 0.8
    
    def test_netflix_entertainment_classification(self):
        """Test classification of Netflix transaction as entertainment."""
        sms_text = "INR 799.00 paid to Netflix via UPI Ref UPI123XYZ on 24-09-2025 0910."
        parsed = self.parser.sms_parser.parse_message(sms_text)
        
        classification = self.classifier.classify_transaction(parsed)
        
        assert classification.category == "entertainment"
        assert classification.confidence >= 0.8

class TestGoalImpactCalculation:
    """Test goal impact calculation functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.goal_calculator = GoalImpactCalculator()
        self.classifier = TransactionClassifier()
        self.parser = TransactionParser()
    
    def test_shopping_budget_impact(self):
        """Test impact of shopping transaction on budget goal."""
        sms_text = "INR 1,249.00 spent on HDFC Credit Card XX1234 at AMAZON on 23-09-2025 1435. Avl Lmt INR 45,670."
        parsed = self.parser.sms_parser.parse_message(sms_text)
        classification = self.classifier.classify_transaction(parsed)
        
        impacts = self.goal_calculator.calculate_transaction_impact(parsed, classification)
        
        # Should impact monthly budget
        budget_impacts = [i for i in impacts if i.goal_id == "monthly-budget"]
        assert len(budget_impacts) > 0
        assert budget_impacts[0].impact_score < 0  # Negative impact on budget

if __name__ == "__main__":
    pytest.main([__file__])
