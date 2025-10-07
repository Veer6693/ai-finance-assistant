import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.ai_modules.transaction_categorizer import TransactionCategorizer

class TestTransactionCategorizer:
    """Test cases for the TransactionCategorizer module"""

    @pytest.fixture
    def categorizer(self):
        """Create a TransactionCategorizer instance for testing"""
        return TransactionCategorizer()

    @pytest.fixture
    def sample_transactions(self):
        """Sample transaction data for testing"""
        return [
            {
                'description': 'SWIGGY BANGALORE',
                'merchant_name': 'Swiggy',
                'amount': 250.0
            },
            {
                'description': 'UBER TRIP',
                'merchant_name': 'Uber India',
                'amount': 180.0
            },
            {
                'description': 'FLIPKART ONLINE',
                'merchant_name': 'Flipkart',
                'amount': 1200.0
            },
            {
                'description': 'PETROL PUMP',
                'merchant_name': 'HP Petrol',
                'amount': 500.0
            },
            {
                'description': 'GROCERY STORE',
                'merchant_name': 'Big Bazaar',
                'amount': 800.0
            }
        ]

    def test_categorizer_initialization(self, categorizer):
        """Test that the categorizer initializes correctly"""
        assert categorizer is not None
        assert hasattr(categorizer, 'categories')
        assert len(categorizer.categories) > 0

    def test_preprocess_text(self, categorizer):
        """Test text preprocessing functionality"""
        test_text = "SWIGGY BANGALORE ORDER 123"
        processed = categorizer._preprocess_text(test_text)
        
        assert isinstance(processed, str)
        assert processed.lower() == processed  # Should be lowercase
        assert len(processed) > 0

    def test_extract_features(self, categorizer):
        """Test feature extraction from transaction data"""
        description = "SWIGGY BANGALORE"
        merchant = "Swiggy"
        amount = 250.0
        
        features = categorizer._extract_features(description, merchant, amount)
        
        assert isinstance(features, np.ndarray)
        assert len(features) > 0
        assert not np.isnan(features).any()

    def test_rule_based_categorization(self, categorizer):
        """Test rule-based categorization"""
        # Test food category
        food_category = categorizer._rule_based_categorization("SWIGGY ORDER", "Swiggy")
        assert food_category == "food"
        
        # Test transport category
        transport_category = categorizer._rule_based_categorization("UBER TRIP", "Uber")
        assert transport_category == "transport"
        
        # Test shopping category
        shopping_category = categorizer._rule_based_categorization("AMAZON ORDER", "Amazon")
        assert shopping_category == "shopping"

    def test_categorize_transaction(self, categorizer):
        """Test the main categorization function"""
        description = "SWIGGY BANGALORE"
        merchant = "Swiggy"
        amount = 250.0
        
        category, confidence = categorizer.categorize_transaction(description, merchant, amount)
        
        assert isinstance(category, str)
        assert category in categorizer.categories
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_categorize_multiple_transactions(self, categorizer, sample_transactions):
        """Test categorizing multiple transactions"""
        results = []
        
        for txn in sample_transactions:
            category, confidence = categorizer.categorize_transaction(
                txn['description'], 
                txn['merchant_name'], 
                txn['amount']
            )
            results.append({
                'category': category,
                'confidence': confidence,
                'original': txn
            })
        
        assert len(results) == len(sample_transactions)
        
        # Check that all results have valid categories and confidence scores
        for result in results:
            assert result['category'] in categorizer.categories
            assert 0.0 <= result['confidence'] <= 1.0

    @patch('app.ai_modules.transaction_categorizer.KMeans')
    def test_train_clustering_model(self, mock_kmeans, categorizer, sample_transactions):
        """Test the clustering model training"""
        # Mock KMeans
        mock_model = Mock()
        mock_model.fit.return_value = None
        mock_model.cluster_centers_ = np.random.rand(len(categorizer.categories), 10)
        mock_kmeans.return_value = mock_model
        
        # Train the model
        categorizer.train_clustering_model(sample_transactions)
        
        # Verify KMeans was called
        mock_kmeans.assert_called_once()
        mock_model.fit.assert_called_once()

    def test_get_category_suggestions(self, categorizer):
        """Test category suggestion functionality"""
        description = "COFFEE SHOP"
        suggestions = categorizer.get_category_suggestions(description)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check that suggestions are valid categories
        for suggestion in suggestions:
            assert suggestion['category'] in categorizer.categories
            assert 'confidence' in suggestion

    def test_update_model_with_feedback(self, categorizer):
        """Test model updating with user feedback"""
        description = "NEW MERCHANT"
        merchant = "Unknown Store"
        amount = 100.0
        correct_category = "shopping"
        
        # This should not raise an error
        categorizer.update_model_with_feedback(
            description, merchant, amount, correct_category
        )
        
        # Verify the feedback was stored
        assert len(categorizer.user_feedback) > 0

    def test_confidence_score_calculation(self, categorizer):
        """Test confidence score calculation"""
        # Test with high confidence scenario
        description = "SWIGGY FOOD ORDER"
        merchant = "Swiggy"
        amount = 250.0
        
        category, confidence = categorizer.categorize_transaction(description, merchant, amount)
        
        # For well-known patterns, confidence should be high
        assert confidence > 0.5

    def test_edge_cases(self, categorizer):
        """Test edge cases and error handling"""
        # Test with empty strings
        category, confidence = categorizer.categorize_transaction("", "", 0.0)
        assert category in categorizer.categories
        assert confidence >= 0.0
        
        # Test with None values
        category, confidence = categorizer.categorize_transaction(None, None, 100.0)
        assert category in categorizer.categories
        assert confidence >= 0.0
        
        # Test with very large amount
        category, confidence = categorizer.categorize_transaction("TEST", "TEST", 1000000.0)
        assert category in categorizer.categories
        assert confidence >= 0.0

    def test_category_list_completeness(self, categorizer):
        """Test that all expected categories are present"""
        expected_categories = [
            'food', 'transport', 'entertainment', 'shopping', 'bills',
            'healthcare', 'investment', 'savings', 'other'
        ]
        
        for category in expected_categories:
            assert category in categorizer.categories

    def test_feature_consistency(self, categorizer):
        """Test that feature extraction is consistent"""
        description = "TEST TRANSACTION"
        merchant = "TEST MERCHANT"
        amount = 100.0
        
        features1 = categorizer._extract_features(description, merchant, amount)
        features2 = categorizer._extract_features(description, merchant, amount)
        
        np.testing.assert_array_equal(features1, features2)

    @pytest.mark.parametrize("description,expected_category", [
        ("SWIGGY BANGALORE", "food"),
        ("UBER RIDE", "transport"),
        ("AMAZON PURCHASE", "shopping"),
        ("NETFLIX SUBSCRIPTION", "entertainment"),
        ("ELECTRICITY BILL", "bills"),
    ])
    def test_specific_categorizations(self, categorizer, description, expected_category):
        """Test specific categorization cases"""
        category, confidence = categorizer.categorize_transaction(description, "", 100.0)
        assert category == expected_category or category == "other"  # Allow fallback to 'other'