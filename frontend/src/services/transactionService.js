import { apiService } from './apiService';

export const transactionService = {
  // Get all transactions for the current user
  async getTransactions(params = {}) {
    try {
      const queryParams = new URLSearchParams(params).toString();
      const url = queryParams ? `/transactions?${queryParams}` : '/transactions';
      return await apiService.get(url);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      // Return empty array as fallback
      return [];
    }
  },

  // Get a specific transaction by ID
  async getTransaction(id) {
    try {
      return await apiService.get(`/v1/transactions/${id}`);
    } catch (error) {
      console.error('Error fetching transaction:', error);
      throw error;
    }
  },

  // Create a new transaction
  async createTransaction(transactionData) {
    try {
      return await apiService.post('/transactions', transactionData);
    } catch (error) {
      console.error('Error creating transaction:', error);
      throw error;
    }
  },

  // Update an existing transaction
  async updateTransaction(id, transactionData) {
    try {
      return await apiService.put(`/transactions/${id}`, transactionData);
    } catch (error) {
      console.error('Error updating transaction:', error);
      throw error;
    }
  },

  // Delete a transaction
  async deleteTransaction(id) {
    try {
      return await apiService.delete(`/transactions/${id}`);
    } catch (error) {
      console.error('Error deleting transaction:', error);
      throw error;
    }
  },

  // Get transaction categories
  async getCategories() {
    try {
      return await apiService.get('/transactions/categories');
    } catch (error) {
      console.error('Error fetching categories:', error);
      // Return default categories as fallback
      return [
        'Food & Dining',
        'Transportation', 
        'Shopping',
        'Entertainment',
        'Bills & Utilities',
        'Healthcare',
        'Investment',
        'Other'
      ];
    }
  },

  // Categorize a transaction using AI
  async categorizeTransaction(transactionData) {
    try {
      return await apiService.post('/transactions/categorize', transactionData);
    } catch (error) {
      console.error('Error categorizing transaction:', error);
      throw error;
    }
  },

  // Get transaction statistics
  async getTransactionStats(period = 'monthly') {
    try {
      return await apiService.get(`/transactions/stats?period=${period}`);
    } catch (error) {
      console.error('Error fetching transaction stats:', error);
      return {};
    }
  }
};