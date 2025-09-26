# @ai perplexity goal-impact-calculator
"""
Goal impact analysis for AmiFi transactions.
Human decisions: Goal definitions, impact scoring algorithms, message generation.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.parsers import ParsedTransaction
from src.classifier import ClassificationResult

class GoalType(Enum):
    """Types of financial goals supported."""
    SAVINGS = "savings"
    BUDGET = "budget" 
    BILL_PAYMENT = "bill_payment"
    SPENDING_LIMIT = "spending_limit"
    INVESTMENT = "investment"

@dataclass
class Goal:
    """Financial goal definition."""
    goal_id: str
    goal_type: GoalType
    name: str
    target_amount: float
    current_amount: float
    deadline: Optional[datetime]
    categories: List[str]  # Categories this goal tracks
    is_active: bool = True

@dataclass
class GoalImpact:
    """Impact of a transaction on a specific goal."""
    goal_id: str
    goal_name: str
    impact_score: float  # -1.0 to +1.0
    message: str
    impact_amount: float
    new_progress: float  # 0.0 to 1.0
    is_goal_achieved: bool
    is_goal_at_risk: bool

class GoalImpactCalculator:
    """Calculate impact of transactions on financial goals."""
    
    def __init__(self):
        # Human decision: Demo goals for the assignment
        self.demo_goals = self._initialize_demo_goals()
    
    def _initialize_demo_goals(self) -> Dict[str, Goal]:
        """Initialize demo goals as specified in assignment."""
        return {
            'demo-savings': Goal(
                goal_id='demo-savings',
                goal_type=GoalType.SAVINGS,
                name='Emergency Fund Savings',
                target_amount=50000.0,
                current_amount=15000.0,  # Demo current progress
                deadline=datetime(2025, 12, 31),
                categories=['credit', 'cashback', 'investment'],
                is_active=True
            ),
            'cc-bill': Goal(
                goal_id='cc-bill',
                goal_type=GoalType.BILL_PAYMENT,
                name='Credit Card Bill Payment',
                target_amount=12450.0,  # From sample data
                current_amount=0.0,
                deadline=datetime(2025, 9, 30),
                categories=['bill', 'credit'],
                is_active=True
            ),
            'monthly-budget': Goal(
                goal_id='monthly-budget',
                goal_type=GoalType.SPENDING_LIMIT,
                name='Monthly Spending Budget',
                target_amount=25000.0,  # Monthly limit
                current_amount=8000.0,  # Demo spent so far
                deadline=datetime(2025, 9, 30),
                categories=['shopping', 'utilities', 'entertainment', 'food_dining'],
                is_active=True
            )
        }
    
    def calculate_transaction_impact(self, 
                                   transaction: ParsedTransaction, 
                                   classification: ClassificationResult) -> List[GoalImpact]:
        """Calculate impact of transaction on all relevant goals."""
        impacts = []
        
        for goal_id, goal in self.demo_goals.items():
            if not goal.is_active:
                continue
                
            impact = self._calculate_single_goal_impact(
                transaction, classification, goal
            )
            
            if impact:  # Only add if transaction affects this goal
                impacts.append(impact)
        
        return impacts
    
    def _calculate_single_goal_impact(self, 
                                    transaction: ParsedTransaction,
                                    classification: ClassificationResult,
                                    goal: Goal) -> Optional[GoalImpact]:
        """Calculate impact on a single goal."""
        
        # Determine if transaction is relevant to this goal
        if not self._is_transaction_relevant(transaction, classification, goal):
            return None
        
        # Calculate impact based on goal type
        if goal.goal_type == GoalType.SAVINGS:
            return self._calculate_savings_impact(transaction, classification, goal)
        elif goal.goal_type == GoalType.BILL_PAYMENT:
            return self._calculate_bill_impact(transaction, classification, goal)
        elif goal.goal_type == GoalType.SPENDING_LIMIT:
            return self._calculate_budget_impact(transaction, classification, goal)
        
        return None
    
    def _is_transaction_relevant(self, 
                               transaction: ParsedTransaction,
                               classification: ClassificationResult, 
                               goal: Goal) -> bool:
        """Check if transaction is relevant to goal."""
        
        # Check if transaction type/category matches goal categories
        if transaction.transaction_type in goal.categories:
            return True
        
        if classification.category in goal.categories:
            return True
        
        # Special cases for bill payments
        if goal.goal_type == GoalType.BILL_PAYMENT:
            if 'reminder' in transaction.raw_message.lower():
                return True
            if goal.goal_id == 'cc-bill' and 'credit card' in transaction.raw_message.lower():
                return True
        
        return False
    
    def _calculate_savings_impact(self, 
                                transaction: ParsedTransaction,
                                classification: ClassificationResult,
                                goal: Goal) -> GoalImpact:
        """Calculate impact on savings goal."""
        
        # Human decision: Savings impact logic
        impact_amount = 0.0
        impact_score = 0.0
        message = ""
        
        if transaction.transaction_type == 'credit':
            # Credits increase savings
            impact_amount = transaction.amount
            impact_score = min(0.8, transaction.amount / 5000)  # Scale impact
            message = f"Great! ₹{transaction.amount:.2f} added to your savings progress"
            
        elif transaction.transaction_type == 'debit':
            # Debits reduce potential savings
            impact_amount = -transaction.amount
            impact_score = -min(0.6, transaction.amount / 5000)
            
            if classification.category == 'shopping' and transaction.amount > 1000:
                message = f"High shopping expense of ₹{transaction.amount:.2f} impacts your savings goal"
            else:
                message = f"₹{transaction.amount:.2f} spent - consider if this aligns with your savings target"
        
        # Calculate new progress
        new_amount = goal.current_amount + impact_amount
        new_progress = min(1.0, max(0.0, new_amount / goal.target_amount))
        
        # Check if goal achieved or at risk
        is_achieved = new_progress >= 1.0
        is_at_risk = (goal.deadline and 
                     (goal.deadline - datetime.now()).days < 30 and 
                     new_progress < 0.5)
        
        return GoalImpact(
            goal_id=goal.goal_id,
            goal_name=goal.name,
            impact_score=impact_score,
            message=message,
            impact_amount=impact_amount,
            new_progress=new_progress,
            is_goal_achieved=is_achieved,
            is_goal_at_risk=is_at_risk
        )
    
    def _calculate_bill_impact(self, 
                             transaction: ParsedTransaction,
                             classification: ClassificationResult,
                             goal: Goal) -> GoalImpact:
        """Calculate impact on bill payment goal."""
        
        impact_amount = 0.0
        impact_score = 0.0
        message = ""
        
        if 'reminder' in transaction.raw_message.lower():
            # Bill reminder - warning impact
            impact_score = -0.9  # High negative impact for reminder
            message = f"⚠️ Bill payment reminder: ₹{transaction.amount:.2f} due soon!"
            impact_amount = transaction.amount
            
        elif transaction.transaction_type == 'credit' and goal.goal_id == 'cc-bill':
            # Payment towards bill
            impact_amount = -transaction.amount  # Reduces bill amount
            impact_score = 0.8
            message = f"✅ ₹{transaction.amount:.2f} payment towards your credit card bill"
        
        # Calculate progress (for bills, progress = amount_paid / total_due)
        remaining_amount = max(0, goal.target_amount + impact_amount)
        new_progress = 1.0 - (remaining_amount / goal.target_amount)
        
        # Check if due date is approaching
        is_at_risk = (goal.deadline and 
                     (goal.deadline - datetime.now()).days <= 5 and 
                     new_progress < 0.8)
        
        if is_at_risk:
            message += " - Due date is approaching!"
        
        return GoalImpact(
            goal_id=goal.goal_id,
            goal_name=goal.name,
            impact_score=impact_score,
            message=message,
            impact_amount=impact_amount,
            new_progress=new_progress,
            is_goal_achieved=new_progress >= 1.0,
            is_goal_at_risk=is_at_risk
        )
    
    def _calculate_budget_impact(self, 
                               transaction: ParsedTransaction,
                               classification: ClassificationResult,
                               goal: Goal) -> GoalImpact:
        """Calculate impact on spending budget goal."""
        
        if transaction.transaction_type != 'debit':
            return None  # Only debits affect spending budget
        
        impact_amount = transaction.amount
        spent_ratio = (goal.current_amount + impact_amount) / goal.target_amount
        
        # Human decision: Budget impact scoring
        if spent_ratio > 1.0:
            impact_score = -1.0  # Exceeded budget
            message = f"⚠️ Budget exceeded! ₹{transaction.amount:.2f} spent on {classification.category}"
        elif spent_ratio > 0.8:
            impact_score = -0.7  # Close to limit
            message = f"⚠️ ₹{transaction.amount:.2f} spent on {classification.category}. You're at {spent_ratio:.0%} of monthly budget"
        else:
            impact_score = -0.3  # Normal spending
            message = f"₹{transaction.amount:.2f} spent on {classification.category}. {(1-spent_ratio):.0%} of budget remaining"
        
        new_progress = min(1.0, spent_ratio)
        
        return GoalImpact(
            goal_id=goal.goal_id,
            goal_name=goal.name,
            impact_score=impact_score,
            message=message,
            impact_amount=impact_amount,
            new_progress=new_progress,
            is_goal_achieved=False,  # Spending goals aren't "achieved"
            is_goal_at_risk=spent_ratio > 0.9
        )
    
    def get_goal_summary(self) -> Dict[str, Dict]:
        """Get summary of all goals and their current status."""
        summary = {}
        
        for goal_id, goal in self.demo_goals.items():
            if goal.is_active:
                progress = goal.current_amount / goal.target_amount
                days_remaining = None
                
                if goal.deadline:
                    days_remaining = (goal.deadline - datetime.now()).days
                
                summary[goal_id] = {
                    'name': goal.name,
                    'type': goal.goal_type.value,
                    'progress': min(1.0, progress),
                    'current_amount': goal.current_amount,
                    'target_amount': goal.target_amount,
                    'days_remaining': days_remaining,
                    'is_on_track': progress >= 0.5 if days_remaining and days_remaining > 30 else None
                }
        
        return summary

# Export for easy imports
__all__ = ['GoalImpactCalculator', 'GoalImpact', 'Goal', 'GoalType']
