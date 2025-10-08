import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  // Generic HTTP methods
  async get(url, params = {}) {
    try {
      const response = await axios.get(`${API_BASE_URL}${url}`, { params });
      return response.data;
    } catch (error) {
      console.error(`GET ${url} error:`, error);
      throw new Error(error.response?.data?.detail || `Failed to fetch from ${url}`);
    }
  }

  async post(url, data = {}) {
    try {
      const response = await axios.post(`${API_BASE_URL}${url}`, data);
      return response.data;
    } catch (error) {
      console.error(`POST ${url} error:`, error);
      throw new Error(error.response?.data?.detail || `Failed to post to ${url}`);
    }
  }

  async put(url, data = {}) {
    try {
      const response = await axios.put(`${API_BASE_URL}${url}`, data);
      return response.data;
    } catch (error) {
      console.error(`PUT ${url} error:`, error);
      throw new Error(error.response?.data?.detail || `Failed to update ${url}`);
    }
  }

  async delete(url) {
    try {
      const response = await axios.delete(`${API_BASE_URL}${url}`);
      return response.data;
    } catch (error) {
      console.error(`DELETE ${url} error:`, error);
      throw new Error(error.response?.data?.detail || `Failed to delete ${url}`);
    }
  }

  // Transactions
  async getTransactions(params = {}) {
    try {
      const response = await axios.get(`${API_BASE_URL}/transactions/`, { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch transactions');
    }
  }

  async createTransaction(transactionData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/transactions/`, transactionData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create transaction');
    }
  }

  async updateTransaction(transactionId, transactionData) {
    try {
      const response = await axios.put(`${API_BASE_URL}/transactions/${transactionId}`, transactionData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update transaction');
    }
  }

  async deleteTransaction(transactionId) {
    try {
      await axios.delete(`${API_BASE_URL}/transactions/${transactionId}`);
      return true;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete transaction');
    }
  }

  async generateDemoTransactions() {
    try {
      const response = await axios.post(`${API_BASE_URL}/transactions/generate-demo`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to generate demo transactions');
    }
  }

  // Analysis
  async getSpendingAnalysis(params = {}) {
    try {
      const response = await axios.get(`${API_BASE_URL}/analysis/spending-summary`, { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch spending analysis');
    }
  }

  async getMonthlyTrends(months = 6) {
    try {
      const response = await axios.get(`${API_BASE_URL}/analysis/monthly-trends`, {
        params: { months }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch monthly trends');
    }
  }

  async getSpendingForecasting(params = {}) {
    try {
      const response = await axios.get(`${API_BASE_URL}/analysis/forecasting`, { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch spending forecast');
    }
  }

  async getAnomalyDetection() {
    try {
      const response = await axios.get(`${API_BASE_URL}/analysis/anomalies`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch anomalies');
    }
  }

  async getBudgetPerformance() {
    try {
      const response = await axios.get(`${API_BASE_URL}/analysis/budget-performance`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch budget performance');
    }
  }

  async getInsights() {
    try {
      const response = await axios.get(`${API_BASE_URL}/analysis/insights`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch insights');
    }
  }

  // AI Chat
  async sendAIQuery(query) {
    try {
      const response = await axios.post(`${API_BASE_URL}/ai-query/process`, { query });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to process AI query');
    }
  }

  async getChatHistory() {
    try {
      const response = await axios.get(`${API_BASE_URL}/ai-query/history`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch chat history');
    }
  }

  // Budget Management
  async getBudgets() {
    try {
      const response = await axios.get(`${API_BASE_URL}/budgets/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch budgets');
    }
  }

  async createBudget(budgetData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/budgets/`, budgetData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create budget');
    }
  }

  async updateBudget(budgetId, budgetData) {
    try {
      const response = await axios.put(`${API_BASE_URL}/budgets/${budgetId}`, budgetData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update budget');
    }
  }

  async deleteBudget(budgetId) {
    try {
      await axios.delete(`${API_BASE_URL}/budgets/${budgetId}`);
      return true;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete budget');
    }
  }

  // Categories
  async getCategories() {
    try {
      const response = await axios.get(`${API_BASE_URL}/categories/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch categories');
    }
  }

  // Dashboard data
  async getDashboardData() {
    try {
      const [
        transactions,
        spendingAnalysis,
        monthlyTrends,
        budgetPerformance,
        insights,
        anomalies
      ] = await Promise.all([
        this.getTransactions({ limit: 10 }),
        this.getSpendingAnalysis(),
        this.getMonthlyTrends(),
        this.getBudgetPerformance(),
        this.getInsights(),
        this.getAnomalyDetection()
      ]);

      return {
        transactions,
        spendingAnalysis,
        monthlyTrends,
        budgetPerformance,
        insights,
        anomalies
      };
    } catch (error) {
      throw new Error('Failed to fetch dashboard data');
    }
  }

  // Export data
  async exportTransactions(format = 'csv', params = {}) {
    try {
      const response = await axios.get(`${API_BASE_URL}/transactions/export`, {
        params: { format, ...params },
        responseType: 'blob'
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const filename = `transactions_${new Date().toISOString().split('T')[0]}.${format}`;
      link.setAttribute('download', filename);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      return true;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to export transactions');
    }
  }

  // UPI Integration
  async getUPIPaymentMethods(amount) {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/payment-methods`, { params: { amount } });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch UPI payment methods');
    }
  }

  async createUPIPayment(paymentData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/upi/create-payment`, paymentData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create UPI payment');
    }
  }

  async getUPIPaymentStatus(paymentId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/payment-status/${paymentId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch UPI payment status');
    }
  }

  async getUPITransactionHistory(limit = 10, skip = 0) {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/transaction-history`, {
        params: { limit, skip }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch UPI transaction history');
    }
  }

  async createUPIPaymentLink(linkData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/upi/create-payment-link`, linkData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create UPI payment link');
    }
  }

  async processUPIRefund(refundData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/upi/refund`, refundData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to process UPI refund');
    }
  }
}

export const apiService = new ApiService();