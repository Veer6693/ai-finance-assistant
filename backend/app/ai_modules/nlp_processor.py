import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

logger = logging.getLogger(__name__)

@dataclass
class QueryIntent:
    """Represents the parsed intent from a user query"""
    intent_type: str  # spending_analysis, budget_query, transaction_search, etc.
    entities: Dict[str, any]  # extracted entities like category, time_period, amount
    confidence: float
    original_query: str

@dataclass
class QueryResponse:
    """Structured response to user query"""
    answer: str
    data: Dict[str, any]
    intent: QueryIntent
    processing_time: float

class NLPQueryProcessor:
    """
    Advanced NLP pipeline for processing natural language queries about financial data.
    Uses BERT/DistilBERT for intent classification and spaCy for entity extraction.
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize models
        self.intent_classifier = None
        self.nlp = None
        self.tokenizer = None
        
        # Intent categories and patterns
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.categories = [
            "food", "groceries", "transport", "shopping", "entertainment",
            "bills", "healthcare", "investment", "education", "income", "other"
        ]
        
        # Initialize models
        self._initialize_models()
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent classification patterns"""
        return {
            "spending_analysis": [
                "how much did i spend",
                "what did i spend on",
                "my spending on",
                "total spent",
                "expenses on",
                "money spent",
                "spending in",
                "expenditure on"
            ],
            "budget_query": [
                "budget for",
                "how much budget",
                "budget remaining",
                "budget left",
                "budget status",
                "budget allocation",
                "my budget"
            ],
            "transaction_search": [
                "find transactions",
                "show transactions",
                "search for",
                "transactions from",
                "payments to",
                "list transactions"
            ],
            "savings_analysis": [
                "how much saved",
                "savings rate",
                "saved money",
                "my savings",
                "total savings"
            ],
            "trend_analysis": [
                "spending trend",
                "spending pattern",
                "monthly trend",
                "spending over time",
                "expense trend"
            ],
            "comparison": [
                "compare spending",
                "spending vs",
                "compared to",
                "difference in spending",
                "spending comparison"
            ],
            "prediction": [
                "predict spending",
                "forecast",
                "next month spending",
                "future expenses",
                "spending prediction"
            ],
            "recommendation": [
                "suggest budget",
                "recommend",
                "advice",
                "optimize budget",
                "budget suggestion"
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """Load entity extraction patterns"""
        return {
            "time_period": {
                "patterns": [
                    r"last (\w+)",
                    r"this (\w+)",
                    r"past (\d+) (\w+)",
                    r"in (\w+)",
                    r"during (\w+)",
                    r"(\w+) (\d{4})",  # month year
                    r"(\d+)/(\d+)",     # month/year
                ],
                "values": {
                    "week": timedelta(weeks=1),
                    "month": timedelta(days=30),
                    "year": timedelta(days=365),
                    "quarter": timedelta(days=90),
                    "today": timedelta(days=1),
                    "yesterday": timedelta(days=1)
                }
            },
            "category": {
                "patterns": [
                    r"on (food|groceries|transport|shopping|entertainment|bills|healthcare|investment|education)",
                    r"for (food|groceries|transport|shopping|entertainment|bills|healthcare|investment|education)",
                    r"(food|groceries|transport|shopping|entertainment|bills|healthcare|investment|education)"
                ]
            },
            "amount": {
                "patterns": [
                    r"₹\s*(\d+(?:,\d+)*(?:\.\d+)?)",
                    r"(\d+(?:,\d+)*(?:\.\d+)?)\s*rupees?",
                    r"(\d+(?:,\d+)*(?:\.\d+)?)\s*rs\.?",
                    r"above ₹\s*(\d+(?:,\d+)*(?:\.\d+)?)",
                    r"below ₹\s*(\d+(?:,\d+)*(?:\.\d+)?)",
                    r"more than ₹\s*(\d+(?:,\d+)*(?:\.\d+)?)",
                    r"less than ₹\s*(\d+(?:,\d+)*(?:\.\d+)?)"
                ]
            },
            "merchant": {
                "patterns": [
                    r"at ([\w\s]+)",
                    r"from ([\w\s]+)",
                    r"to ([\w\s]+)",
                    r"(swiggy|zomato|uber|ola|amazon|flipkart|netflix|spotify)"
                ]
            }
        }
    
    def _initialize_models(self):
        """Initialize NLP models"""
        try:
            # Load spaCy model for entity extraction
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
            
            # Initialize BERT-based intent classifier
            # For demo, we'll use a simple sentiment classifier and adapt it
            self.intent_classifier = pipeline(
                "text-classification",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
            logger.info("Intent classifier loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NLP models: {e}")
            # Fallback to rule-based processing
            self.nlp = None
            self.intent_classifier = None
    
    def classify_intent(self, query: str) -> Tuple[str, float]:
        """
        Classify the intent of the user query.
        
        Returns:
            Tuple of (intent_type, confidence)
        """
        query_lower = query.lower()
        
        # Rule-based intent classification
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    confidence = 0.8 + (len(pattern) / len(query_lower)) * 0.2
                    return intent_type, min(confidence, 0.95)
        
        # If no direct match, use ML-based classification (simplified)
        if self.intent_classifier:
            try:
                # For demo, map sentiment to likely intents
                result = self.intent_classifier(query)[0]
                
                # Simple mapping (in real implementation, train custom classifier)
                if "spending" in query_lower or "spent" in query_lower:
                    return "spending_analysis", 0.7
                elif "budget" in query_lower:
                    return "budget_query", 0.7
                elif "find" in query_lower or "search" in query_lower:
                    return "transaction_search", 0.7
                else:
                    return "spending_analysis", 0.5  # Default
                    
            except Exception as e:
                logger.error(f"Error in ML intent classification: {e}")
        
        # Default fallback
        return "spending_analysis", 0.3
    
    def extract_entities(self, query: str) -> Dict[str, any]:
        """
        Extract entities from the query using spaCy and regex patterns.
        
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract time periods
        time_entities = self._extract_time_entities(query)
        if time_entities:
            entities.update(time_entities)
        
        # Extract categories
        category_entity = self._extract_category(query)
        if category_entity:
            entities["category"] = category_entity
        
        # Extract amounts
        amount_entities = self._extract_amounts(query)
        if amount_entities:
            entities.update(amount_entities)
        
        # Extract merchants
        merchant_entity = self._extract_merchant(query)
        if merchant_entity:
            entities["merchant"] = merchant_entity
        
        # Use spaCy for additional entity extraction
        if self.nlp:
            try:
                doc = self.nlp(query)
                for ent in doc.ents:
                    if ent.label_ == "MONEY" and "amount" not in entities:
                        entities["amount"] = self._parse_money_entity(ent.text)
                    elif ent.label_ == "DATE" and "time_period" not in entities:
                        entities["time_period"] = self._parse_date_entity(ent.text)
                    elif ent.label_ in ["ORG", "PERSON"] and "merchant" not in entities:
                        entities["merchant"] = ent.text.strip()
            except Exception as e:
                logger.error(f"Error in spaCy entity extraction: {e}")
        
        return entities
    
    def _extract_time_entities(self, query: str) -> Dict[str, any]:
        """Extract time-related entities"""
        entities = {}
        query_lower = query.lower()
        
        # Common time patterns
        time_mappings = {
            "today": {"start_date": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                     "end_date": datetime.now()},
            "yesterday": {"start_date": (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                         "end_date": datetime.now() - timedelta(days=1)},
            "this week": {"start_date": datetime.now() - timedelta(days=datetime.now().weekday()),
                         "end_date": datetime.now()},
            "last week": {"start_date": datetime.now() - timedelta(days=datetime.now().weekday() + 7),
                         "end_date": datetime.now() - timedelta(days=datetime.now().weekday())},
            "this month": {"start_date": datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                          "end_date": datetime.now()},
            "last month": {"start_date": (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1),
                          "end_date": datetime.now().replace(day=1) - timedelta(days=1)},
            "this year": {"start_date": datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                         "end_date": datetime.now()},
            "last year": {"start_date": datetime.now().replace(year=datetime.now().year-1, month=1, day=1),
                         "end_date": datetime.now().replace(year=datetime.now().year-1, month=12, day=31)}
        }
        
        for time_phrase, dates in time_mappings.items():
            if time_phrase in query_lower:
                entities["time_period"] = time_phrase
                entities["start_date"] = dates["start_date"]
                entities["end_date"] = dates["end_date"]
                break
        
        # Extract specific numbers of days/weeks/months
        past_pattern = re.search(r"past (\d+) (days?|weeks?|months?|years?)", query_lower)
        if past_pattern:
            number = int(past_pattern.group(1))
            unit = past_pattern.group(2)
            
            if "day" in unit:
                start_date = datetime.now() - timedelta(days=number)
            elif "week" in unit:
                start_date = datetime.now() - timedelta(weeks=number)
            elif "month" in unit:
                start_date = datetime.now() - timedelta(days=number * 30)
            elif "year" in unit:
                start_date = datetime.now() - timedelta(days=number * 365)
            
            entities["time_period"] = f"past {number} {unit}"
            entities["start_date"] = start_date
            entities["end_date"] = datetime.now()
        
        return entities
    
    def _extract_category(self, query: str) -> Optional[str]:
        """Extract spending category from query"""
        query_lower = query.lower()
        
        # Direct category mentions
        for category in self.categories:
            if category in query_lower:
                return category
        
        # Category synonyms
        category_synonyms = {
            "food": ["eating", "dining", "restaurant", "meal", "lunch", "dinner", "breakfast"],
            "groceries": ["grocery", "supermarket", "vegetables", "fruits", "household"],
            "transport": ["travel", "commute", "cab", "taxi", "fuel", "petrol", "metro", "bus"],
            "shopping": ["clothes", "electronics", "gadgets", "purchase", "buy", "online"],
            "entertainment": ["movie", "cinema", "music", "game", "streaming", "subscription"],
            "bills": ["utility", "electricity", "gas", "internet", "mobile", "recharge"],
            "healthcare": ["medical", "doctor", "hospital", "medicine", "pharmacy", "health"],
            "investment": ["stocks", "shares", "mutual fund", "sip", "insurance", "savings"],
            "education": ["course", "learning", "books", "tuition", "training", "skill"]
        }
        
        for category, synonyms in category_synonyms.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    return category
        
        return None
    
    def _extract_amounts(self, query: str) -> Dict[str, any]:
        """Extract amount-related entities"""
        entities = {}
        
        # Amount patterns
        amount_patterns = [
            r"₹\s*(\d+(?:,\d+)*(?:\.\d+)?)",
            r"(\d+(?:,\d+)*(?:\.\d+)?)\s*rupees?",
            r"(\d+(?:,\d+)*(?:\.\d+)?)\s*rs\.?",
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    entities["amount"] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Amount comparisons
        if "above" in query.lower() or "more than" in query.lower():
            entities["amount_comparison"] = "greater_than"
        elif "below" in query.lower() or "less than" in query.lower():
            entities["amount_comparison"] = "less_than"
        elif "exactly" in query.lower() or "equal to" in query.lower():
            entities["amount_comparison"] = "equal_to"
        
        return entities
    
    def _extract_merchant(self, query: str) -> Optional[str]:
        """Extract merchant/store names from query"""
        common_merchants = [
            "swiggy", "zomato", "uber", "ola", "amazon", "flipkart", "myntra",
            "netflix", "spotify", "bookmyshow", "airtel", "jio", "apollo",
            "dmart", "big bazaar", "reliance", "pvr", "inox", "mcdonald",
            "kfc", "domino", "starbucks", "cafe coffee day"
        ]
        
        query_lower = query.lower()
        for merchant in common_merchants:
            if merchant in query_lower:
                return merchant.title()
        
        # Extract from "at/from/to" patterns
        patterns = [r"at ([\w\s]+)", r"from ([\w\s]+)", r"to ([\w\s]+)"]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                potential_merchant = match.group(1).strip()
                if len(potential_merchant) > 2 and potential_merchant.lower() not in ["the", "a", "an"]:
                    return potential_merchant.title()
        
        return None
    
    def _parse_money_entity(self, text: str) -> Optional[float]:
        """Parse money entity from spaCy"""
        # Remove currency symbols and convert to float
        amount_str = re.sub(r'[₹$,]', '', text)
        try:
            return float(amount_str)
        except ValueError:
            return None
    
    def _parse_date_entity(self, text: str) -> str:
        """Parse date entity from spaCy"""
        # Simplified date parsing
        return text.lower()
    
    def process_query(self, query: str, user_context: Optional[Dict] = None) -> QueryIntent:
        """
        Process a natural language query and extract structured information.
        
        Args:
            query: User's natural language query
            user_context: Optional context about the user
            
        Returns:
            QueryIntent object with processed information
        """
        start_time = datetime.now()
        
        # Classify intent
        intent_type, confidence = self.classify_intent(query)
        
        # Extract entities
        entities = self.extract_entities(query)
        
        # Add user context if available
        if user_context:
            entities["user_id"] = user_context.get("user_id")
            entities["user_preferences"] = user_context.get("preferences", {})
        
        # Create QueryIntent object
        query_intent = QueryIntent(
            intent_type=intent_type,
            entities=entities,
            confidence=confidence,
            original_query=query
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Query processed in {processing_time:.3f}s: {intent_type} (confidence: {confidence:.2f})")
        
        return query_intent
    
    def generate_sql_query(self, query_intent: QueryIntent) -> str:
        """
        Generate SQL query based on processed intent.
        This is a simplified version - in production, use proper SQL query builders.
        """
        entities = query_intent.entities
        intent_type = query_intent.intent_type
        
        base_query = "SELECT * FROM transactions WHERE user_id = :user_id"
        conditions = []
        
        # Add time filters
        if "start_date" in entities and "end_date" in entities:
            conditions.append("transaction_date BETWEEN :start_date AND :end_date")
        
        # Add category filter
        if "category" in entities:
            conditions.append("ai_category = :category")
        
        # Add amount filter
        if "amount" in entities:
            comparison = entities.get("amount_comparison", "equal_to")
            if comparison == "greater_than":
                conditions.append("amount > :amount")
            elif comparison == "less_than":
                conditions.append("amount < :amount")
            else:
                conditions.append("amount = :amount")
        
        # Add merchant filter
        if "merchant" in entities:
            conditions.append("merchant_name ILIKE :merchant")
        
        # Combine conditions
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add aggregations based on intent
        if intent_type == "spending_analysis":
            if "category" in entities:
                base_query = f"SELECT SUM(amount) as total_spent FROM ({base_query}) as filtered_transactions"
            else:
                base_query = f"SELECT ai_category, SUM(amount) as total_spent FROM ({base_query}) as filtered_transactions GROUP BY ai_category"
        
        return base_query
    
    def format_response(self, query_intent: QueryIntent, data: any) -> str:
        """
        Format the response in natural language based on the query intent and data.
        """
        intent_type = query_intent.intent_type
        entities = query_intent.entities
        
        if intent_type == "spending_analysis":
            if isinstance(data, dict) and "total_spent" in data:
                amount = data["total_spent"] or 0
                category = entities.get("category", "all categories")
                time_period = entities.get("time_period", "all time")
                
                return f"You spent ₹{amount:,.2f} on {category} during {time_period}."
            
            elif isinstance(data, list):
                total = sum(item.get("total_spent", 0) for item in data)
                category_breakdown = ", ".join([
                    f"{item['ai_category']}: ₹{item['total_spent']:,.2f}" 
                    for item in data[:3]  # Top 3 categories
                ])
                
                time_period = entities.get("time_period", "the selected period")
                return f"During {time_period}, you spent a total of ₹{total:,.2f}. Top categories: {category_breakdown}."
        
        elif intent_type == "budget_query":
            # Handle budget-related responses
            return "Here's your budget information..."
        
        elif intent_type == "transaction_search":
            if isinstance(data, list):
                count = len(data)
                return f"Found {count} transactions matching your criteria."
        
        # Default response
        return "I found some information based on your query. Please check the detailed results."

# Example usage and testing
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "How much did I spend on food last month?",
        "Show me my budget for transport this month",
        "Find transactions from Swiggy above ₹500",
        "What's my total spending this week?",
        "Compare my spending this month vs last month",
        "Predict my next month's food expenses"
    ]
    
    # Initialize processor
    processor = NLPQueryProcessor()
    
    # Process test queries
    for query in test_queries:
        print(f"\nQuery: {query}")
        intent = processor.process_query(query)
        print(f"Intent: {intent.intent_type} (confidence: {intent.confidence:.2f})")
        print(f"Entities: {intent.entities}")
        
        # Generate SQL (for demonstration)
        sql = processor.generate_sql_query(intent)
        print(f"Generated SQL: {sql}")
        print("-" * 50)