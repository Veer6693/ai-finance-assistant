import re
import json
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TransactionCategorizer:
    """
    AI-powered transaction categorization using K-means clustering and rule-based classification.
    Combines unsupervised learning with domain-specific rules for accurate categorization.
    """
    
    def __init__(self, model_path: str = "trained_models/categorizer"):
        self.model_path = model_path
        self.categories = [
            "food", "groceries", "transport", "shopping", "entertainment", 
            "bills", "healthcare", "investment", "education", "income", "other"
        ]
        
        # Initialize components
        self.kmeans_model = None
        self.tfidf_vectorizer = None
        self.scaler = None
        self.category_rules = self._load_category_rules()
        self.merchant_patterns = self._load_merchant_patterns()
        
        # Performance tracking
        self.categorization_stats = {
            "total_processed": 0,
            "rule_based_matches": 0,
            "ml_predictions": 0,
            "accuracy_score": 0.0
        }
    
    def _load_category_rules(self) -> Dict[str, List[str]]:
        """Load rule-based categorization patterns"""
        return {
            "food": [
                r"swiggy|zomato|food|restaurant|cafe|pizza|burger|mcdonald|kfc|domino",
                r"dinner|lunch|breakfast|snacks|meal|dining|eatery|kitchen",
                r"hotel.*restaurant|food.*order|online.*food"
            ],
            "groceries": [
                r"big bazaar|dmart|reliance fresh|grocery|supermarket|vegetables",
                r"blinkit|bigbasket|grofers|fresh|market|provision",
                r"weekly.*shopping|household.*items|grocery.*store"
            ],
            "transport": [
                r"uber|ola|auto|taxi|cab|metro|bus|train|flight|petrol|diesel",
                r"transport|travel|fuel|parking|toll|vehicle|rapido",
                r"airport|railway|station|booking.*travel"
            ],
            "shopping": [
                r"amazon|flipkart|myntra|ajio|nykaa|shopping|mall|store",
                r"clothes|dress|shirt|shoes|electronics|mobile|laptop",
                r"online.*purchase|ecommerce|retail|fashion"
            ],
            "entertainment": [
                r"netflix|prime|hotstar|spotify|bookmyshow|movie|cinema|pvr|inox",
                r"entertainment|game|music|subscription|streaming|concert",
                r"ticket.*movie|gaming|recreation|leisure"
            ],
            "bills": [
                r"electricity|gas|water|internet|mobile.*recharge|bill|utility",
                r"airtel|jio|bsnl|broadband|wifi|recharge|dth|cable",
                r"municipal|society.*maintenance|maintenance.*charges"
            ],
            "healthcare": [
                r"hospital|clinic|doctor|medicine|pharmacy|apollo|1mg|netmeds",
                r"medical|health|dentist|lab.*test|checkup|treatment",
                r"pharma|drug|prescription|healthcare|wellness"
            ],
            "investment": [
                r"sip|mutual fund|stock|share|zerodha|groww|investment|insurance",
                r"trading|equity|bond|fd|ppf|epf|ulip|portfolio",
                r"financial.*planning|wealth|savings.*plan"
            ],
            "education": [
                r"course|education|school|college|university|tuition|fee",
                r"udemy|coursera|unacademy|byju|book|learning|training",
                r"educational|skill.*development|certification"
            ],
            "income": [
                r"salary|income|payment.*received|credit.*transfer|refund",
                r"freelance|consulting|bonus|incentive|dividend|interest",
                r"received.*from|credited.*by|income.*tax.*refund"
            ]
        }
    
    def _load_merchant_patterns(self) -> Dict[str, str]:
        """Load merchant name to category mappings"""
        return {
            # Food & Dining
            "swiggy": "food", "zomato": "food", "mcdonald": "food", "kfc": "food",
            "domino": "food", "pizza hut": "food", "subway": "food", "starbucks": "food",
            
            # Groceries
            "big bazaar": "groceries", "dmart": "groceries", "reliance fresh": "groceries",
            "blinkit": "groceries", "bigbasket": "groceries", "grofers": "groceries",
            
            # Transport
            "uber": "transport", "ola": "transport", "rapido": "transport",
            "metro": "transport", "petrol pump": "transport", "indian oil": "transport",
            
            # Shopping
            "amazon": "shopping", "flipkart": "shopping", "myntra": "shopping",
            "ajio": "shopping", "nykaa": "shopping", "lifestyle": "shopping",
            
            # Entertainment
            "netflix": "entertainment", "amazon prime": "entertainment", "spotify": "entertainment",
            "bookmyshow": "entertainment", "pvr": "entertainment", "inox": "entertainment",
            
            # Bills
            "airtel": "bills", "jio": "bills", "bsnl": "bills", "electricity board": "bills",
            "gas authority": "bills", "broadband": "bills",
            
            # Healthcare
            "apollo": "healthcare", "1mg": "healthcare", "netmeds": "healthcare",
            "pharmeasy": "healthcare", "hospital": "healthcare",
            
            # Investment
            "zerodha": "investment", "groww": "investment", "sbi mutual fund": "investment",
            "lic": "investment", "hdfc bank": "investment",
            
            # Education
            "udemy": "education", "coursera": "education", "unacademy": "education",
            "byju": "education", "school": "education"
        }
    
    def preprocess_transaction_text(self, description: str, merchant_name: str) -> str:
        """Preprocess transaction text for ML features"""
        text = f"{description} {merchant_name}".lower()
        
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove special characters
        text = re.sub(r'\d+', 'NUM', text)   # Replace numbers with NUM token
        text = re.sub(r'\s+', ' ', text)      # Normalize whitespace
        
        return text.strip()
    
    def extract_features(self, transactions: List[Dict]) -> np.ndarray:
        """Extract features for ML model"""
        features = []
        
        for txn in transactions:
            # Text features
            text = self.preprocess_transaction_text(
                txn.get('description', ''), 
                txn.get('merchant_name', '')
            )
            
            # Temporal features
            txn_date = txn.get('transaction_date')
            if isinstance(txn_date, str):
                txn_date = datetime.fromisoformat(txn_date)
            
            # Numerical features
            feature_vector = {
                'amount_log': np.log1p(float(txn.get('amount', 0))),
                'hour': txn_date.hour if txn_date else 12,
                'day_of_week': txn_date.weekday() if txn_date else 0,
                'is_weekend': (txn_date.weekday() >= 5) if txn_date else False,
                'description_length': len(txn.get('description', '')),
                'merchant_length': len(txn.get('merchant_name', '')),
                'text': text
            }
            
            features.append(feature_vector)
        
        return features
    
    def categorize_by_rules(self, description: str, merchant_name: str) -> Tuple[Optional[str], float]:
        """
        Categorize transaction using rule-based approach.
        
        Returns:
            Tuple of (category, confidence_score)
        """
        text = f"{description} {merchant_name}".lower()
        
        # Check merchant patterns first (highest confidence)
        for merchant, category in self.merchant_patterns.items():
            if merchant in text:
                return category, 0.95
        
        # Check category rules
        for category, patterns in self.category_rules.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return category, 0.85
        
        return None, 0.0
    
    def train_ml_model(self, transactions: List[Dict], labels: List[str]) -> Dict:
        """
        Train K-means clustering model for transaction categorization.
        
        Args:
            transactions: List of transaction dictionaries
            labels: List of category labels
            
        Returns:
            Training metrics and model info
        """
        logger.info(f"Training categorization model with {len(transactions)} transactions")
        
        # Extract features
        feature_data = self.extract_features(transactions)
        
        # Prepare text features
        texts = [f['text'] for f in feature_data]
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500, 
            stop_words='english', 
            ngram_range=(1, 2)
        )
        text_features = self.tfidf_vectorizer.fit_transform(texts).toarray()
        
        # Prepare numerical features
        numerical_features = np.array([
            [f['amount_log'], f['hour'], f['day_of_week'], 
             f['is_weekend'], f['description_length'], f['merchant_length']]
            for f in feature_data
        ])
        
        # Scale numerical features
        self.scaler = StandardScaler()
        numerical_features_scaled = self.scaler.fit_transform(numerical_features)
        
        # Combine features
        combined_features = np.hstack([text_features, numerical_features_scaled])
        
        # Train K-means model
        n_clusters = min(len(self.categories), len(set(labels)))
        self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans_model.fit_predict(combined_features)
        
        # Map clusters to categories (simplified mapping)
        cluster_to_category = self._map_clusters_to_categories(cluster_labels, labels)
        
        # Save models
        self.save_models()
        
        # Calculate accuracy
        predicted_categories = [cluster_to_category.get(cluster, 'other') for cluster in cluster_labels]
        accuracy = accuracy_score(labels, predicted_categories)
        
        training_metrics = {
            "model_type": "K-means + Rule-based",
            "n_clusters": n_clusters,
            "n_features": combined_features.shape[1],
            "accuracy": accuracy,
            "training_samples": len(transactions),
            "categories": self.categories,
            "cluster_mapping": cluster_to_category
        }
        
        logger.info(f"Model trained successfully. Accuracy: {accuracy:.3f}")
        return training_metrics
    
    def _map_clusters_to_categories(self, cluster_labels: np.ndarray, true_labels: List[str]) -> Dict:
        """Map cluster IDs to category names"""
        cluster_to_category = {}
        
        for cluster_id in set(cluster_labels):
            # Find most common category in this cluster
            cluster_mask = cluster_labels == cluster_id
            cluster_true_labels = [true_labels[i] for i, mask in enumerate(cluster_mask) if mask]
            
            if cluster_true_labels:
                # Most frequent category in cluster
                category_counts = {}
                for cat in cluster_true_labels:
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                most_common = max(category_counts.items(), key=lambda x: x[1])[0]
                cluster_to_category[cluster_id] = most_common
            else:
                cluster_to_category[cluster_id] = 'other'
        
        return cluster_to_category
    
    def predict_category(self, transaction: Dict) -> Tuple[str, float]:
        """
        Predict category for a single transaction.
        
        Returns:
            Tuple of (category, confidence_score)
        """
        description = transaction.get('description', '')
        merchant_name = transaction.get('merchant_name', '')
        
        # Try rule-based first
        rule_category, rule_confidence = self.categorize_by_rules(description, merchant_name)
        if rule_category:
            self.categorization_stats["rule_based_matches"] += 1
            return rule_category, rule_confidence
        
        # Fall back to ML model
        if self.kmeans_model is None:
            logger.warning("ML model not trained. Using 'other' category.")
            return "other", 0.1
        
        try:
            # Extract features for single transaction
            features = self.extract_features([transaction])
            
            # Transform features
            text = features[0]['text']
            text_features = self.tfidf_vectorizer.transform([text]).toarray()
            
            numerical_features = np.array([[
                features[0]['amount_log'], features[0]['hour'], 
                features[0]['day_of_week'], features[0]['is_weekend'],
                features[0]['description_length'], features[0]['merchant_length']
            ]])
            numerical_features_scaled = self.scaler.transform(numerical_features)
            
            # Combine features
            combined_features = np.hstack([text_features, numerical_features_scaled])
            
            # Predict cluster
            cluster = self.kmeans_model.predict(combined_features)[0]
            
            # Map cluster to category
            cluster_to_category = getattr(self, 'cluster_to_category', {})
            category = cluster_to_category.get(cluster, 'other')
            
            # Calculate confidence based on distance to cluster center
            distances = self.kmeans_model.transform(combined_features)[0]
            min_distance = np.min(distances)
            confidence = max(0.1, 1.0 - (min_distance / np.max(distances)))
            
            self.categorization_stats["ml_predictions"] += 1
            return category, confidence
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return "other", 0.1
    
    def categorize_batch(self, transactions: List[Dict]) -> List[Dict]:
        """
        Categorize multiple transactions efficiently.
        
        Returns:
            List of dictionaries with categorization results
        """
        results = []
        
        for txn in transactions:
            category, confidence = self.predict_category(txn)
            
            result = {
                "transaction_id": txn.get("transaction_id"),
                "predicted_category": category,
                "confidence_score": confidence,
                "original_merchant_category": txn.get("merchant_category"),
                "method": "rule_based" if confidence > 0.8 else "ml_model"
            }
            results.append(result)
            
            self.categorization_stats["total_processed"] += 1
        
        return results
    
    def save_models(self):
        """Save trained models to disk"""
        import os
        os.makedirs(self.model_path, exist_ok=True)
        
        if self.kmeans_model:
            joblib.dump(self.kmeans_model, f"{self.model_path}/kmeans_model.pkl")
        if self.tfidf_vectorizer:
            joblib.dump(self.tfidf_vectorizer, f"{self.model_path}/tfidf_vectorizer.pkl")
        if self.scaler:
            joblib.dump(self.scaler, f"{self.model_path}/scaler.pkl")
        
        # Save cluster mapping if available
        if hasattr(self, 'cluster_to_category'):
            with open(f"{self.model_path}/cluster_mapping.json", 'w') as f:
                json.dump(self.cluster_to_category, f)
        
        logger.info(f"Models saved to {self.model_path}")
    
    def load_models(self):
        """Load trained models from disk"""
        import os
        
        try:
            if os.path.exists(f"{self.model_path}/kmeans_model.pkl"):
                self.kmeans_model = joblib.load(f"{self.model_path}/kmeans_model.pkl")
            if os.path.exists(f"{self.model_path}/tfidf_vectorizer.pkl"):
                self.tfidf_vectorizer = joblib.load(f"{self.model_path}/tfidf_vectorizer.pkl")
            if os.path.exists(f"{self.model_path}/scaler.pkl"):
                self.scaler = joblib.load(f"{self.model_path}/scaler.pkl")
            
            # Load cluster mapping
            if os.path.exists(f"{self.model_path}/cluster_mapping.json"):
                with open(f"{self.model_path}/cluster_mapping.json", 'r') as f:
                    self.cluster_to_category = json.load(f)
            
            logger.info("Models loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def get_categorization_stats(self) -> Dict:
        """Get categorization performance statistics"""
        total = self.categorization_stats["total_processed"]
        if total == 0:
            return self.categorization_stats
        
        stats = self.categorization_stats.copy()
        stats["rule_based_percentage"] = (stats["rule_based_matches"] / total) * 100
        stats["ml_prediction_percentage"] = (stats["ml_predictions"] / total) * 100
        
        return stats
    
    def update_model_with_feedback(self, transaction_id: str, correct_category: str):
        """Update model with user feedback (for future implementation)"""
        # This would implement online learning to improve model accuracy
        # For now, just log the feedback
        logger.info(f"Feedback received: Transaction {transaction_id} should be categorized as {correct_category}")
        
        # TODO: Implement incremental learning or retrain periodically with feedback

# Example usage and testing
if __name__ == "__main__":
    # Example transactions for testing
    sample_transactions = [
        {
            "transaction_id": "TXN001",
            "description": "Swiggy Food Order",
            "merchant_name": "Swiggy",
            "amount": 350.0,
            "transaction_date": datetime.now()
        },
        {
            "transaction_id": "TXN002", 
            "description": "Uber Ride",
            "merchant_name": "Uber India",
            "amount": 150.0,
            "transaction_date": datetime.now()
        }
    ]
    
    # Initialize categorizer
    categorizer = TransactionCategorizer()
    
    # Test rule-based categorization
    for txn in sample_transactions:
        category, confidence = categorizer.predict_category(txn)
        print(f"Transaction: {txn['description']}")
        print(f"Predicted Category: {category} (Confidence: {confidence:.2f})")
        print("---")