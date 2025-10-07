import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import logging
from dataclasses import dataclass
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

logger = logging.getLogger(__name__)

@dataclass
class BudgetAction:
    """Represents a budget recommendation action"""
    category: str
    recommended_amount: float
    current_amount: float
    change_percentage: float
    reasoning: str
    confidence: float

@dataclass
class UserContext:
    """User context for contextual bandit"""
    user_id: int
    income: float
    savings_goal: float
    risk_tolerance: str  # conservative, moderate, aggressive
    spending_patterns: Dict[str, float]
    historical_performance: Dict[str, float]
    current_month_spending: Dict[str, float]
    goals_achieved: List[str]
    month_day: int
    is_weekend: bool

class ContextualBudgetOptimizer:
    """
    Contextual bandit algorithm for personalized budget optimization.
    Learns user preferences and optimizes budget allocations based on spending behavior.
    """
    
    def __init__(self, model_path: str = "trained_models/budget_optimizer"):
        self.model_path = model_path
        
        # Categories for budget optimization
        self.categories = [
            "food", "groceries", "transport", "shopping", "entertainment",
            "bills", "healthcare", "investment", "education", "savings"
        ]
        
        # Action space: budget adjustment percentages
        self.action_space = [-0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2]  # -20% to +20%
        
        # Contextual bandit components
        self.reward_models = {}  # One model per category
        self.feature_scaler = StandardScaler()
        self.exploration_rate = 0.1  # Epsilon for epsilon-greedy exploration
        
        # Performance tracking
        self.recommendation_history = []
        self.user_feedback = {}
        self.model_performance = {}
        
        # Budget optimization rules
        self.optimization_rules = self._load_optimization_rules()
        
        # Initialize models
        self._initialize_reward_models()
    
    def _load_optimization_rules(self) -> Dict:
        """Load budget optimization rules and constraints"""
        return {
            "essential_categories": ["groceries", "bills", "healthcare", "transport"],
            "discretionary_categories": ["entertainment", "shopping", "food"],
            "investment_categories": ["investment", "savings"],
            "minimum_allocation": {
                "groceries": 0.05,    # Minimum 5% of income
                "bills": 0.1,         # Minimum 10% of income
                "transport": 0.05,    # Minimum 5% of income
                "healthcare": 0.02,   # Minimum 2% of income
                "savings": 0.1        # Minimum 10% of income
            },
            "maximum_allocation": {
                "entertainment": 0.15,  # Maximum 15% of income
                "shopping": 0.2,        # Maximum 20% of income
                "food": 0.25           # Maximum 25% of income
            },
            "risk_tolerance_multipliers": {
                "conservative": {"investment": 0.8, "discretionary": 0.9},
                "moderate": {"investment": 1.0, "discretionary": 1.0},
                "aggressive": {"investment": 1.3, "discretionary": 1.1}
            }
        }
    
    def _initialize_reward_models(self):
        """Initialize reward prediction models for each category"""
        for category in self.categories:
            # Use different models for different types of categories
            if category in ["investment", "savings"]:
                # Linear model for financial categories
                self.reward_models[category] = Ridge(alpha=1.0)
            else:
                # Random Forest for spending categories
                self.reward_models[category] = RandomForestRegressor(
                    n_estimators=50, 
                    max_depth=10, 
                    random_state=42
                )
    
    def extract_context_features(self, user_context: UserContext) -> np.ndarray:
        """
        Extract features from user context for the contextual bandit.
        
        Args:
            user_context: Current user context
            
        Returns:
            Feature vector for the bandit algorithm
        """
        features = []
        
        # Basic user features
        features.extend([
            user_context.income / 100000,  # Normalized income
            user_context.savings_goal / user_context.income if user_context.income > 0 else 0,
            len(user_context.goals_achieved) / 10,  # Normalized goals achieved
            user_context.month_day / 31,  # Day of month (0-1)
            1.0 if user_context.is_weekend else 0.0
        ])
        
        # Risk tolerance (one-hot encoded)
        risk_encodings = {"conservative": [1, 0, 0], "moderate": [0, 1, 0], "aggressive": [0, 0, 1]}
        features.extend(risk_encodings.get(user_context.risk_tolerance, [0, 1, 0]))
        
        # Spending patterns (last 3 months average)
        for category in self.categories:
            avg_spending = user_context.spending_patterns.get(category, 0)
            features.append(avg_spending / user_context.income if user_context.income > 0 else 0)
        
        # Current month spending progress
        for category in self.categories:
            current_spending = user_context.current_month_spending.get(category, 0)
            features.append(current_spending / user_context.income if user_context.income > 0 else 0)
        
        # Historical performance (budget adherence)
        for category in self.categories:
            performance = user_context.historical_performance.get(category, 0.5)  # Default 50%
            features.append(performance)
        
        return np.array(features)
    
    def calculate_reward(self, 
                        action: BudgetAction, 
                        user_context: UserContext,
                        actual_outcome: Optional[Dict] = None) -> float:
        """
        Calculate reward for a budget recommendation.
        
        Args:
            action: The budget action taken
            user_context: User context when action was taken
            actual_outcome: Actual results after action (for learning)
            
        Returns:
            Reward score (higher is better)
        """
        reward = 0.0
        
        # Base reward components
        category = action.category
        recommended_amount = action.recommended_amount
        
        # 1. Budget feasibility reward
        income_percentage = recommended_amount / user_context.income if user_context.income > 0 else 0
        
        # Penalize unrealistic budgets
        if category in self.optimization_rules["minimum_allocation"]:
            min_required = self.optimization_rules["minimum_allocation"][category]
            if income_percentage < min_required:
                reward -= 0.3  # Penalty for insufficient essential allocation
        
        if category in self.optimization_rules["maximum_allocation"]:
            max_allowed = self.optimization_rules["maximum_allocation"][category]
            if income_percentage > max_allowed:
                reward -= 0.2  # Penalty for excessive allocation
        
        # 2. Alignment with user preferences reward
        historical_avg = user_context.spending_patterns.get(category, 0)
        if historical_avg > 0:
            deviation = abs(recommended_amount - historical_avg) / historical_avg
            reward += 0.2 * (1 - min(deviation, 1.0))  # Reward for reasonable deviation
        
        # 3. Risk tolerance alignment
        risk_multipliers = self.optimization_rules["risk_tolerance_multipliers"][user_context.risk_tolerance]
        
        if category in ["investment", "savings"]:
            investment_multiplier = risk_multipliers["investment"]
            if (investment_multiplier > 1.0 and action.change_percentage > 0) or \
               (investment_multiplier < 1.0 and action.change_percentage < 0):
                reward += 0.2
        
        # 4. Goal achievement potential
        if category == "savings" and user_context.savings_goal > 0:
            projected_savings = recommended_amount * 12  # Annual projection
            goal_achievement_ratio = projected_savings / user_context.savings_goal
            reward += 0.3 * min(goal_achievement_ratio, 1.0)
        
        # 5. Actual outcome reward (if available)
        if actual_outcome:
            budget_adherence = actual_outcome.get("budget_adherence", 0.5)
            user_satisfaction = actual_outcome.get("user_satisfaction", 0.5)
            goal_progress = actual_outcome.get("goal_progress", 0.5)
            
            reward += 0.3 * budget_adherence
            reward += 0.2 * user_satisfaction
            reward += 0.2 * goal_progress
        
        # 6. Confidence-based reward
        reward += 0.1 * action.confidence
        
        return max(0.0, min(1.0, reward))  # Clamp to [0, 1]
    
    def select_budget_action(self, 
                           user_context: UserContext, 
                           category: str,
                           current_budget: float) -> BudgetAction:
        """
        Select optimal budget action using contextual bandit algorithm.
        
        Args:
            user_context: Current user context
            category: Budget category to optimize
            current_budget: Current budget amount for the category
            
        Returns:
            Recommended budget action
        """
        context_features = self.extract_context_features(user_context)
        
        # Exploration vs exploitation
        if np.random.random() < self.exploration_rate:
            # Exploration: random action
            action_index = np.random.choice(len(self.action_space))
            confidence = 0.3  # Lower confidence for random exploration
        else:
            # Exploitation: use trained model
            action_index, confidence = self._predict_best_action(context_features, category, current_budget)
        
        # Calculate new budget amount
        change_percentage = self.action_space[action_index]
        new_amount = current_budget * (1 + change_percentage)
        
        # Apply constraints
        new_amount = self._apply_budget_constraints(
            category, new_amount, user_context.income, user_context.risk_tolerance
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(category, change_percentage, user_context)
        
        action = BudgetAction(
            category=category,
            recommended_amount=new_amount,
            current_amount=current_budget,
            change_percentage=(new_amount - current_budget) / current_budget if current_budget > 0 else 0,
            reasoning=reasoning,
            confidence=confidence
        )
        
        return action
    
    def _predict_best_action(self, 
                           context_features: np.ndarray, 
                           category: str, 
                           current_budget: float) -> Tuple[int, float]:
        """
        Predict the best action using trained reward models.
        """
        if category not in self.reward_models:
            return 3, 0.5  # Default to no change with medium confidence
        
        model = self.reward_models[category]
        
        # If model is not trained, return default
        if not hasattr(model, 'predict'):
            return 3, 0.3
        
        try:
            # Predict rewards for all possible actions
            action_rewards = []
            
            for action_idx, change_pct in enumerate(self.action_space):
                # Create feature vector for this action
                action_features = np.concatenate([
                    context_features,
                    [change_pct, current_budget / 10000]  # Add action-specific features
                ])
                
                # Predict reward
                if hasattr(model, 'predict'):
                    reward = model.predict([action_features])[0]
                else:
                    reward = 0.5  # Default
                
                action_rewards.append(reward)
            
            # Select action with highest predicted reward
            best_action_idx = np.argmax(action_rewards)
            confidence = min(0.9, max(0.1, action_rewards[best_action_idx]))
            
            return best_action_idx, confidence
            
        except Exception as e:
            logger.error(f"Error predicting action for {category}: {e}")
            return 3, 0.3  # Default to no change
    
    def _apply_budget_constraints(self, 
                                category: str, 
                                amount: float, 
                                income: float, 
                                risk_tolerance: str) -> float:
        """Apply budget constraints and limits"""
        if income <= 0:
            return amount
        
        # Apply minimum constraints
        if category in self.optimization_rules["minimum_allocation"]:
            min_amount = income * self.optimization_rules["minimum_allocation"][category]
            amount = max(amount, min_amount)
        
        # Apply maximum constraints
        if category in self.optimization_rules["maximum_allocation"]:
            max_amount = income * self.optimization_rules["maximum_allocation"][category]
            amount = min(amount, max_amount)
        
        # Apply risk tolerance adjustments
        risk_multipliers = self.optimization_rules["risk_tolerance_multipliers"][risk_tolerance]
        
        if category in ["investment", "savings"]:
            amount *= risk_multipliers["investment"]
        elif category in self.optimization_rules["discretionary_categories"]:
            amount *= risk_multipliers["discretionary"]
        
        return max(0, amount)
    
    def _generate_reasoning(self, 
                          category: str, 
                          change_percentage: float, 
                          user_context: UserContext) -> str:
        """Generate human-readable reasoning for budget recommendation"""
        if abs(change_percentage) < 0.01:
            return f"Your current {category} budget is well-balanced based on your spending patterns and goals."
        
        direction = "increase" if change_percentage > 0 else "decrease"
        percentage = abs(change_percentage) * 100
        
        reasons = []
        
        # Category-specific reasoning
        if category == "savings":
            if change_percentage > 0:
                reasons.append(f"to help you reach your savings goal of ₹{user_context.savings_goal:,.0f}")
            else:
                reasons.append("to free up funds for other essential expenses")
        
        elif category in ["investment"]:
            if change_percentage > 0 and user_context.risk_tolerance == "aggressive":
                reasons.append("based on your aggressive investment risk tolerance")
            elif change_percentage < 0 and user_context.risk_tolerance == "conservative":
                reasons.append("aligned with your conservative investment approach")
        
        elif category in self.optimization_rules["essential_categories"]:
            if change_percentage > 0:
                reasons.append("to ensure adequate coverage of essential expenses")
            else:
                reasons.append("as your current allocation seems sufficient")
        
        elif category in self.optimization_rules["discretionary_categories"]:
            if change_percentage < 0:
                reasons.append("to optimize your spending on discretionary items")
            else:
                reasons.append("to improve your lifestyle within reasonable limits")
        
        # Historical performance reasoning
        historical_performance = user_context.historical_performance.get(category, 0.5)
        if historical_performance < 0.7 and change_percentage < 0:
            reasons.append("since you've been exceeding this budget consistently")
        elif historical_performance > 0.9 and change_percentage > 0:
            reasons.append("as you've been staying well within this budget")
        
        base_reason = f"I recommend you {direction} your {category} budget by {percentage:.1f}%"
        if reasons:
            return f"{base_reason} {' and '.join(reasons)}."
        else:
            return f"{base_reason} based on your spending patterns and financial goals."
    
    def optimize_complete_budget(self, user_context: UserContext, current_budgets: Dict[str, float]) -> Dict[str, BudgetAction]:
        """
        Optimize the complete budget across all categories.
        
        Args:
            user_context: Current user context
            current_budgets: Current budget allocations
            
        Returns:
            Dictionary of optimized budget actions for each category
        """
        recommendations = {}
        
        # First pass: individual category optimization
        for category in self.categories:
            current_budget = current_budgets.get(category, 0)
            action = self.select_budget_action(user_context, category, current_budget)
            recommendations[category] = action
        
        # Second pass: ensure total budget doesn't exceed income
        total_recommended = sum(action.recommended_amount for action in recommendations.values())
        
        if total_recommended > user_context.income * 0.95:  # Leave 5% buffer
            # Scale down discretionary categories
            excess = total_recommended - (user_context.income * 0.95)
            discretionary_total = sum(
                recommendations[cat].recommended_amount 
                for cat in self.optimization_rules["discretionary_categories"]
                if cat in recommendations
            )
            
            if discretionary_total > 0:
                reduction_factor = max(0.7, 1 - (excess / discretionary_total))
                
                for category in self.optimization_rules["discretionary_categories"]:
                    if category in recommendations:
                        action = recommendations[category]
                        new_amount = action.recommended_amount * reduction_factor
                        
                        recommendations[category] = BudgetAction(
                            category=category,
                            recommended_amount=new_amount,
                            current_amount=action.current_amount,
                            change_percentage=(new_amount - action.current_amount) / action.current_amount if action.current_amount > 0 else 0,
                            reasoning=f"{action.reasoning} (Adjusted to fit total budget constraints)",
                            confidence=action.confidence * 0.9
                        )
        
        return recommendations
    
    def update_models_with_feedback(self, 
                                  user_context: UserContext,
                                  actions_taken: Dict[str, BudgetAction],
                                  outcomes: Dict[str, Dict]) -> None:
        """
        Update reward models based on user feedback and actual outcomes.
        
        Args:
            user_context: Context when actions were taken
            actions_taken: Budget actions that were implemented
            outcomes: Actual results for each category
        """
        context_features = self.extract_context_features(user_context)
        
        for category, action in actions_taken.items():
            if category in outcomes and category in self.reward_models:
                outcome = outcomes[category]
                reward = self.calculate_reward(action, user_context, outcome)
                
                # Prepare training data
                action_idx = min(range(len(self.action_space)), 
                               key=lambda i: abs(self.action_space[i] - action.change_percentage))
                
                features = np.concatenate([
                    context_features,
                    [self.action_space[action_idx], action.current_amount / 10000]
                ])
                
                # Update model (simplified online learning)
                try:
                    model = self.reward_models[category]
                    if hasattr(model, 'partial_fit'):
                        model.partial_fit([features], [reward])
                    else:
                        # For models without partial_fit, store data for batch retraining
                        if not hasattr(self, 'training_data'):
                            self.training_data = {}
                        if category not in self.training_data:
                            self.training_data[category] = {'X': [], 'y': []}
                        
                        self.training_data[category]['X'].append(features)
                        self.training_data[category]['y'].append(reward)
                        
                        # Retrain periodically
                        if len(self.training_data[category]['X']) >= 10:
                            X = np.array(self.training_data[category]['X'])
                            y = np.array(self.training_data[category]['y'])
                            model.fit(X, y)
                            self.training_data[category] = {'X': [], 'y': []}
                
                except Exception as e:
                    logger.error(f"Error updating model for {category}: {e}")
        
        # Update exploration rate (decay over time)
        self.exploration_rate = max(0.05, self.exploration_rate * 0.995)
    
    def get_budget_insights(self, 
                          user_context: UserContext,
                          current_budgets: Dict[str, float]) -> Dict:
        """
        Generate insights about current budget allocation.
        """
        total_budget = sum(current_budgets.values())
        income_utilization = total_budget / user_context.income if user_context.income > 0 else 0
        
        insights = {
            "budget_summary": {
                "total_allocated": total_budget,
                "income_utilization": income_utilization,
                "remaining_income": max(0, user_context.income - total_budget),
                "allocation_breakdown": {
                    cat: (amount / total_budget * 100) if total_budget > 0 else 0
                    for cat, amount in current_budgets.items()
                }
            },
            "risk_assessment": self._assess_budget_risk(user_context, current_budgets),
            "optimization_opportunities": self._identify_optimization_opportunities(user_context, current_budgets),
            "goal_alignment": self._assess_goal_alignment(user_context, current_budgets)
        }
        
        return insights
    
    def _assess_budget_risk(self, user_context: UserContext, budgets: Dict[str, float]) -> Dict:
        """Assess risk level of current budget allocation"""
        total_essential = sum(budgets.get(cat, 0) for cat in self.optimization_rules["essential_categories"])
        total_discretionary = sum(budgets.get(cat, 0) for cat in self.optimization_rules["discretionary_categories"])
        total_investment = sum(budgets.get(cat, 0) for cat in self.optimization_rules["investment_categories"])
        
        essential_ratio = total_essential / user_context.income if user_context.income > 0 else 0
        discretionary_ratio = total_discretionary / user_context.income if user_context.income > 0 else 0
        investment_ratio = total_investment / user_context.income if user_context.income > 0 else 0
        
        risk_level = "low"
        if essential_ratio < 0.3:
            risk_level = "high"  # Too little for essentials
        elif discretionary_ratio > 0.4:
            risk_level = "high"  # Too much discretionary spending
        elif essential_ratio > 0.7:
            risk_level = "medium"  # Very conservative
        
        return {
            "level": risk_level,
            "essential_ratio": essential_ratio,
            "discretionary_ratio": discretionary_ratio,
            "investment_ratio": investment_ratio,
            "recommendations": self._get_risk_recommendations(risk_level)
        }
    
    def _identify_optimization_opportunities(self, user_context: UserContext, budgets: Dict[str, float]) -> List[str]:
        """Identify opportunities for budget optimization"""
        opportunities = []
        
        # Check for under-allocation in important categories
        savings_allocation = budgets.get("savings", 0) / user_context.income if user_context.income > 0 else 0
        if savings_allocation < 0.1:
            opportunities.append("Consider increasing savings allocation to at least 10% of income")
        
        # Check for over-allocation in discretionary categories
        for category in ["entertainment", "shopping"]:
            allocation = budgets.get(category, 0) / user_context.income if user_context.income > 0 else 0
            max_recommended = self.optimization_rules["maximum_allocation"].get(category, 0.2)
            if allocation > max_recommended:
                opportunities.append(f"Consider reducing {category} budget from {allocation*100:.1f}% to {max_recommended*100:.1f}% of income")
        
        return opportunities
    
    def _assess_goal_alignment(self, user_context: UserContext, budgets: Dict[str, float]) -> Dict:
        """Assess how well budget aligns with financial goals"""
        savings_budget = budgets.get("savings", 0)
        investment_budget = budgets.get("investment", 0)
        
        annual_savings = (savings_budget + investment_budget) * 12
        goal_progress = annual_savings / user_context.savings_goal if user_context.savings_goal > 0 else 1
        
        return {
            "savings_goal_progress": min(1.0, goal_progress),
            "annual_savings_projection": annual_savings,
            "months_to_goal": user_context.savings_goal / (savings_budget + investment_budget) if (savings_budget + investment_budget) > 0 else float('inf'),
            "alignment_score": min(1.0, goal_progress)
        }
    
    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = {
            "low": ["Your budget allocation looks balanced", "Consider increasing investment allocation if possible"],
            "medium": ["Review discretionary spending for optimization opportunities", "Ensure emergency fund is adequate"],
            "high": ["Prioritize essential categories", "Reduce discretionary spending", "Build emergency fund"]
        }
        return recommendations.get(risk_level, [])
    
    def save_models(self):
        """Save trained models and data"""
        import os
        os.makedirs(self.model_path, exist_ok=True)
        
        # Save reward models
        for category, model in self.reward_models.items():
            if hasattr(model, 'fit'):  # Only save trained models
                joblib.dump(model, f"{self.model_path}/{category}_reward_model.pkl")
        
        # Save scaler
        joblib.dump(self.feature_scaler, f"{self.model_path}/feature_scaler.pkl")
        
        # Save metadata
        metadata = {
            "categories": self.categories,
            "action_space": self.action_space,
            "exploration_rate": self.exploration_rate,
            "model_performance": self.model_performance
        }
        
        with open(f"{self.model_path}/metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        logger.info(f"Budget optimizer models saved to {self.model_path}")
    
    def load_models(self):
        """Load trained models and data"""
        import os
        
        try:
            # Load reward models
            for category in self.categories:
                model_path = f"{self.model_path}/{category}_reward_model.pkl"
                if os.path.exists(model_path):
                    self.reward_models[category] = joblib.load(model_path)
            
            # Load scaler
            scaler_path = f"{self.model_path}/feature_scaler.pkl"
            if os.path.exists(scaler_path):
                self.feature_scaler = joblib.load(scaler_path)
            
            # Load metadata
            metadata_path = f"{self.model_path}/metadata.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.exploration_rate = metadata.get("exploration_rate", 0.1)
                    self.model_performance = metadata.get("model_performance", {})
            
            logger.info("Budget optimizer models loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Example usage with mock data
    optimizer = ContextualBudgetOptimizer()
    
    # Mock user context
    user_context = UserContext(
        user_id=1,
        income=50000,
        savings_goal=100000,
        risk_tolerance="moderate",
        spending_patterns={"food": 8000, "transport": 5000, "entertainment": 3000},
        historical_performance={"food": 0.8, "transport": 0.9, "entertainment": 0.6},
        current_month_spending={"food": 2000, "transport": 1500, "entertainment": 1000},
        goals_achieved=["emergency_fund"],
        month_day=15,
        is_weekend=False
    )
    
    # Mock current budgets
    current_budgets = {
        "food": 8000,
        "transport": 5000,
        "entertainment": 3000,
        "groceries": 6000,
        "bills": 4000,
        "savings": 5000
    }
    
    # Get budget recommendations
    recommendations = optimizer.optimize_complete_budget(user_context, current_budgets)
    
    print("Budget Recommendations:")
    for category, action in recommendations.items():
        print(f"{category}: ₹{action.current_amount} → ₹{action.recommended_amount:.0f} "
              f"({action.change_percentage*100:+.1f}%)")
        print(f"  Reasoning: {action.reasoning}")
        print(f"  Confidence: {action.confidence:.2f}")
        print()