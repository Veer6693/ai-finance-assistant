import { apiService } from './apiService';

export const budgetService = {
  // Get all budgets for the current user
  async getBudgets() {
    try {
      return await apiService.get('/v1/budgets');
    } catch (error) {
      console.error('Error fetching budgets:', error);
      // Return empty array as fallback
      return [];
    }
  },

  // Get a specific budget by ID
  async getBudget(id) {
    try {
      return await apiService.get(`/v1/budgets/${id}`);
    } catch (error) {
      console.error('Error fetching budget:', error);
      throw error;
    }
  },

  // Create a new budget
  async createBudget(budgetData) {
    try {
      return await apiService.post('/v1/budgets', budgetData);
    } catch (error) {
      console.error('Error creating budget:', error);
      throw error;
    }
  },

  // Update an existing budget
  async updateBudget(id, budgetData) {
    try {
      return await apiService.put(`/v1/budgets/${id}`, budgetData);
    } catch (error) {
      console.error('Error updating budget:', error);
      throw error;
    }
  },

  // Delete a budget
  async deleteBudget(id) {
    try {
      return await apiService.delete(`/v1/budgets/${id}`);
    } catch (error) {
      console.error('Error deleting budget:', error);
      throw error;
    }
  },

  // Get budget performance/analytics
  async getBudgetPerformance(budgetId, period = 'current') {
    try {
      return await apiService.get(`/v1/budgets/${budgetId}/performance?period=${period}`);
    } catch (error) {
      console.error('Error fetching budget performance:', error);
      return {};
    }
  },

  // Get budget recommendations
  async getBudgetRecommendations() {
    try {
      return await apiService.get('/budgets/recommendations');
    } catch (error) {
      console.error('Error fetching budget recommendations:', error);
      return [];
    }
  },

  // Get budget overview/summary
  async getBudgetOverview() {
    try {
      return await apiService.get('/budgets/overview');
    } catch (error) {
      console.error('Error fetching budget overview:', error);
      return {};
    }
  }
};