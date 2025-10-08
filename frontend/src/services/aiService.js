import { apiService } from './apiService';

export const aiService = {
  // Process natural language query
  async processQuery(query) {
    try {
      const response = await apiService.post('/ai/query', { query });
      return response;
    } catch (error) {
      console.error('Error processing AI query:', error);
      throw error;
    }
  },

  // Get categories (using available backend endpoint)
  async getCategories() {
    try {
      return await apiService.get('/ai/categories');
    } catch (error) {
      console.error('Error fetching categories:', error);
      return [];
    }
  },

  // Get AI model status (using available backend endpoint)
  async getModelStatus() {
    try {
      return await apiService.get('/ai/model-status');
    } catch (error) {
      console.error('Error fetching AI model status:', error);
      return { status: 'unknown' };
    }
  },

  // Chat history management (local storage for now)
  async getQueryHistory(limit = 10) {
    try {
      const history = JSON.parse(localStorage.getItem('aiChatHistory') || '[]');
      return history.slice(-limit);
    } catch (error) {
      console.error('Error fetching query history:', error);
      return [];
    }
  },

  async saveToHistory(query, response) {
    try {
      const history = JSON.parse(localStorage.getItem('aiChatHistory') || '[]');
      history.push({
        id: Date.now(),
        query,
        response,
        timestamp: new Date().toISOString()
      });
      // Keep only last 50 entries
      if (history.length > 50) {
        history.splice(0, history.length - 50);
      }
      localStorage.setItem('aiChatHistory', JSON.stringify(history));
    } catch (error) {
      console.error('Error saving to history:', error);
    }
  },

  // Placeholder methods for features not yet implemented in backend
  async getSpendingInsights(period = 'monthly') {
    console.log('Spending insights not yet implemented in backend');
    return {
      message: "AI insights feature is under development. Use the chat to ask specific questions about your finances."
    };
  },

  async getSpendingForecast(months = 3) {
    console.log('Spending forecast not yet implemented in backend');
    return {
      message: "Spending forecast feature is under development. Use the chat to ask about spending predictions."
    };
  },

  async getBudgetRecommendations() {
    console.log('Budget recommendations not yet implemented in backend');
    return {
      message: "AI recommendations feature is under development. Use the chat to ask for spending advice."
    };
  },

  async getAnomalies(period = 'recent') {
    console.log('Anomaly detection not yet implemented in backend');
    return {
      message: "Anomaly detection feature is under development. Use the chat to ask about unusual transactions."
    };
  },

  // Legacy method name for compatibility
  async getSystemStatus() {
    return this.getModelStatus();
  }
};