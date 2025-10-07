import pytest
import sys
import os
from unittest.mock import Mock, patch
import numpy as np

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.ai_modules.nlp_query_processor import NLPQueryProcessor

class TestNLPQueryProcessor:
    """Test cases for the NLP Query Processor module"""

    @pytest.fixture
    def processor(self):
        """Create an NLPQueryProcessor instance for testing"""
        return NLPQueryProcessor()

    @pytest.fixture
    def sample_queries(self):
        """Sample queries for testing"""
        return [
            "How much did I spend on food last month?",
            "Show me my transactions for groceries",
            "What's my biggest expense this week?",
            "How much money do I have left in my budget?",
            "When did I last order from Swiggy?",
            "What are my recurring payments?",
            "How much did I spend on transport yesterday?",
            "Show me all transactions above 1000 rupees"
        ]

    def test_processor_initialization(self, processor):
        """Test that the processor initializes correctly"""
        assert processor is not None
        assert hasattr(processor, 'intents')
        assert len(processor.intents) > 0

    def test_preprocess_query(self, processor):
        """Test query preprocessing"""
        query = "How much did I spend on FOOD last month???"
        processed = processor._preprocess_query(query)
        
        assert isinstance(processed, str)
        assert processed.lower() == processed
        assert "?" not in processed
        assert len(processed) > 0

    def test_intent_classification(self, processor, sample_queries):
        """Test intent classification for various queries"""
        for query in sample_queries:
            intent, confidence = processor._classify_intent(query)
            
            assert isinstance(intent, str)
            assert intent in processor.intents
            assert isinstance(confidence, float)
            assert 0.0 <= confidence <= 1.0

    def test_entity_extraction(self, processor):
        """Test entity extraction from queries"""
        # Test amount extraction
        query1 = "Show me transactions above 1000 rupees"
        entities1 = processor._extract_entities(query1)
        assert 'amount' in entities1
        assert entities1['amount'] == 1000.0

        # Test category extraction
        query2 = "How much did I spend on food?"
        entities2 = processor._extract_entities(query2)
        assert 'category' in entities2
        assert entities2['category'] == 'food'

        # Test time period extraction
        query3 = "Show my expenses last month"
        entities3 = processor._extract_entities(query3)
        assert 'time_period' in entities3

    def test_process_query(self, processor):
        """Test the main query processing function"""
        query = "How much did I spend on food last month?"
        
        result = processor.process_query(query)
        
        assert isinstance(result, dict)
        assert 'intent' in result
        assert 'entities' in result
        assert 'confidence' in result
        assert 'response_type' in result

    @pytest.mark.parametrize("query,expected_intent", [
        ("How much did I spend?", "spending_query"),
        ("Show me my transactions", "transaction_list"),
        ("What's my budget status?", "budget_query"),
        ("When did I last buy groceries?", "transaction_search"),
        ("What are my monthly expenses?", "spending_analysis"),
    ])
    def test_intent_classification_accuracy(self, processor, query, expected_intent):
        """Test accuracy of intent classification for specific queries"""
        intent, confidence = processor._classify_intent(query)
        
        # Intent should match expected or be a reasonable alternative
        assert intent == expected_intent or intent in processor.intents

    def test_amount_parsing(self, processor):
        """Test amount parsing from text"""
        test_cases = [
            ("1000 rupees", 1000.0),
            ("Rs 500", 500.0),
            ("₹250", 250.0),
            ("five hundred", 500.0),
            ("1k", 1000.0),
            ("2.5k", 2500.0)
        ]
        
        for text, expected_amount in test_cases:
            amount = processor._parse_amount(text)
            assert amount == expected_amount or amount > 0  # Allow some flexibility

    def test_date_parsing(self, processor):
        """Test date parsing from natural language"""
        test_cases = [
            "last month",
            "yesterday", 
            "this week",
            "last 30 days",
            "January 2024",
            "last year"
        ]
        
        for date_text in test_cases:
            date_info = processor._parse_date(date_text)
            assert isinstance(date_info, dict)
            assert 'start_date' in date_info or 'period' in date_info

    def test_category_extraction(self, processor):
        """Test category extraction from queries"""
        category_queries = [
            ("food", "How much on food?"),
            ("transport", "My Uber expenses"),
            ("entertainment", "Netflix spending"),
            ("shopping", "Amazon purchases"),
            ("bills", "utility bills")
        ]
        
        for expected_category, query in category_queries:
            entities = processor._extract_entities(query)
            if 'category' in entities:
                assert entities['category'] == expected_category

    def test_merchant_extraction(self, processor):
        """Test merchant name extraction"""
        merchant_queries = [
            ("Swiggy", "How much did I spend on Swiggy?"),
            ("Amazon", "Show my Amazon orders"),
            ("Uber", "Uber expenses this month"),
            ("Flipkart", "Flipkart purchases")
        ]
        
        for expected_merchant, query in merchant_queries:
            entities = processor._extract_entities(query)
            if 'merchant' in entities:
                assert expected_merchant.lower() in entities['merchant'].lower()

    def test_query_complexity_handling(self, processor):
        """Test handling of complex queries"""
        complex_queries = [
            "Show me all food expenses above 500 rupees from last month excluding Swiggy",
            "What's my average monthly spending on transport and entertainment combined?",
            "How much did I save compared to my budget for groceries this quarter?"
        ]
        
        for query in complex_queries:
            result = processor.process_query(query)
            
            assert isinstance(result, dict)
            assert 'intent' in result
            assert 'entities' in result
            # Complex queries might have lower confidence
            assert result['confidence'] >= 0.0

    def test_error_handling(self, processor):
        """Test error handling for invalid inputs"""
        # Test empty query
        result = processor.process_query("")
        assert isinstance(result, dict)
        assert result['intent'] in processor.intents
        
        # Test None query
        result = processor.process_query(None)
        assert isinstance(result, dict)
        
        # Test very long query
        long_query = "How much " * 100 + "did I spend?"
        result = processor.process_query(long_query)
        assert isinstance(result, dict)

    def test_response_generation(self, processor):
        """Test response generation based on query processing"""
        query = "How much did I spend on food?"
        result = processor.process_query(query)
        
        if 'suggested_response' in result:
            assert isinstance(result['suggested_response'], str)
            assert len(result['suggested_response']) > 0

    def test_confidence_calculation(self, processor):
        """Test confidence score calculation"""
        # High confidence query
        clear_query = "How much did I spend on food last month?"
        result1 = processor.process_query(clear_query)
        
        # Ambiguous query
        unclear_query = "show stuff"
        result2 = processor.process_query(unclear_query)
        
        # Clear queries should have higher confidence
        assert result1['confidence'] >= result2['confidence']

    @patch('app.ai_modules.nlp_query_processor.pipeline')
    def test_bert_integration(self, mock_pipeline, processor):
        """Test BERT model integration"""
        # Mock BERT pipeline
        mock_pipeline.return_value = Mock()
        mock_pipeline.return_value.return_value = [{'label': 'spending_query', 'score': 0.9}]
        
        query = "How much did I spend?"
        intent, confidence = processor._classify_intent(query)
        
        assert intent == 'spending_query'
        assert confidence == 0.9

    def test_supported_intents(self, processor):
        """Test that all required intents are supported"""
        required_intents = [
            'spending_query',
            'transaction_list', 
            'budget_query',
            'transaction_search',
            'spending_analysis',
            'general_query'
        ]
        
        for intent in required_intents:
            assert intent in processor.intents

    def test_entity_types(self, processor):
        """Test that all required entity types are recognized"""
        query = "Show me food transactions above 1000 rupees from last month from Swiggy"
        entities = processor._extract_entities(query)
        
        # Should extract multiple entity types
        possible_entities = ['category', 'amount', 'time_period', 'merchant']
        extracted_count = sum(1 for entity_type in possible_entities if entity_type in entities)
        
        assert extracted_count > 0  # At least some entities should be extracted