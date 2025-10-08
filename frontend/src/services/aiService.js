import { apiService } from './apiService';

export const aiService = {
  // Process natural language query
  async processQuery(query) {
    try {
      const response = await apiService.post('/v1/ai/process', { query });
      return response;
    } catch (error) {
      console.error('Error processing AI query:', error);
      throw error;
    }
  },

  // Get AI query history
  async getQueryHistory(limit = 10) {
    try {
      return await apiService.get(`/v1/ai/history?limit=${limit}`);
    } catch (error) {
      console.error('Error fetching query history:', error);
      return [];
    }
  },

  // Get spending insights
  async getSpendingInsights(period = 'monthly') {
    try {
      return await apiService.get(`/v1/ai/insights/spending?period=${period}`);
    } catch (error) {
      console.error('Error fetching spending insights:', error);
      return {};
    }
  },

  // Get spending forecast
  async getSpendingForecast(months = 3) {
    try {
      return await apiService.get(`/v1/ai/forecast?months=${months}`);
    } catch (error) {
      console.error('Error fetching spending forecast:', error);
      return {};
    }
  },

  // Get budget recommendations from AI
  async getBudgetRecommendations() {
    try {
      return await apiService.get('/v1/ai/recommendations/budget');
    } catch (error) {
      console.error('Error fetching AI budget recommendations:', error);
      return [];
    }
  },

  // Get anomaly detection results
  async getAnomalies(period = 'recent') {
    try {
      return await apiService.get(`/ai/anomalies?period=${period}`);
    } catch (error) {
      console.error('Error fetching anomalies:', error);
      return [];
    }
  },

  // Get AI system status
  async getSystemStatus() {
    try {
      return await apiService.get('/ai/status');
    } catch (error) {
      console.error('Error fetching AI system status:', error);
      return { status: 'unknown' };
    }
  }
};