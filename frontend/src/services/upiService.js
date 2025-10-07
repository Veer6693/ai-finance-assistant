import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class UPIService {
  // Get available payment methods
  async getPaymentMethods(amount) {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/payment-methods`, {
        params: { amount }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch payment methods');
    }
  }

  // Create UPI payment
  async createPayment(paymentData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/upi/create-payment`, paymentData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create payment');
    }
  }

  // Create payment link
  async createPaymentLink(linkData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/upi/create-payment-link`, linkData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create payment link');
    }
  }

  // Get payment status
  async getPaymentStatus(paymentId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/payment-status/${paymentId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch payment status');
    }
  }

  // Get transaction history
  async getTransactionHistory(limit = 10, skip = 0) {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/transaction-history`, {
        params: { limit, skip }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch transaction history');
    }
  }

  // Process refund
  async processRefund(refundData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/upi/refund`, refundData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to process refund');
    }
  }

  // Get UPI providers
  async getProviders() {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/providers`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch providers');
    }
  }

  // Get mock accounts (for testing)
  async getMockAccounts() {
    try {
      const response = await axios.get(`${API_BASE_URL}/upi/mock-accounts`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch mock accounts');
    }
  }

  // Validate VPA format
  validateVPA(vpa) {
    if (!vpa) return false;
    
    // Basic VPA format: username@provider
    const vpaRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+$/;
    return vpaRegex.test(vpa);
  }

  // Validate UPI amount
  validateAmount(amount) {
    const numAmount = parseFloat(amount);
    return !isNaN(numAmount) && numAmount > 0 && numAmount <= 200000; // UPI limit
  }

  // Format UPI transaction for display
  formatTransaction(transaction) {
    return {
      id: transaction.id,
      paymentId: transaction.payment_id || transaction.id,
      amount: transaction.amount,
      status: transaction.status,
      vpa: transaction.vpa,
      provider: transaction.provider,
      description: transaction.description,
      createdAt: new Date(transaction.created_at * 1000), // Convert from timestamp
      capturedAt: transaction.captured_at ? new Date(transaction.captured_at * 1000) : null,
      errorCode: transaction.error_code,
      errorDescription: transaction.error_description
    };
  }

  // Get status color for UI
  getStatusColor(status) {
    switch (status) {
      case 'captured':
        return 'success';
      case 'failed':
        return 'error';
      case 'pending':
        return 'warning';
      case 'created':
        return 'info';
      default:
        return 'default';
    }
  }

  // Get status display text
  getStatusText(status) {
    switch (status) {
      case 'captured':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Processing';
      case 'created':
        return 'Initiated';
      default:
        return 'Unknown';
    }
  }

  // Generate QR code data for UPI payment
  generateUPIQRCode(vpa, amount, description, merchantName = 'FinanceAI') {
    // UPI QR code format: upi://pay?pa=VPA&pn=Name&am=Amount&tn=Description
    const params = new URLSearchParams({
      pa: vpa, // Payee address
      pn: merchantName, // Payee name
      am: amount.toString(), // Amount
      tn: description, // Transaction note
      cu: 'INR' // Currency
    });
    
    return `upi://pay?${params.toString()}`;
  }

  // Check if payment method is supported
  isPaymentMethodSupported(method) {
    const supportedMethods = ['upi', 'card', 'netbanking', 'wallet'];
    return supportedMethods.includes(method.toLowerCase());
  }

  // Get provider logo URL
  getProviderLogo(provider) {
    const logoMap = {
      paytm: '/assets/logos/paytm.png',
      phonepe: '/assets/logos/phonepe.png',
      googlepay: '/assets/logos/googlepay.png',
      amazonpay: '/assets/logos/amazonpay.png',
      bhim: '/assets/logos/bhim.png'
    };
    
    return logoMap[provider?.toLowerCase()] || '/assets/logos/upi.png';
  }

  // Calculate processing time estimate
  getProcessingTimeEstimate(amount) {
    if (amount <= 1000) {
      return '2-5 seconds';
    } else if (amount <= 10000) {
      return '5-10 seconds';
    } else {
      return '10-30 seconds';
    }
  }

  // Get transaction limits
  getTransactionLimits() {
    return {
      minimum: 1, // ₹1
      maximum: 200000, // ₹2,00,000 per transaction
      dailyLimit: 1000000, // ₹10,00,000 per day
      monthlyLimit: 10000000 // ₹1,00,00,000 per month
    };
  }

  // Check if amount is within limits
  isAmountWithinLimits(amount) {
    const limits = this.getTransactionLimits();
    return amount >= limits.minimum && amount <= limits.maximum;
  }

  // Format error message for user
  formatErrorMessage(errorCode, errorDescription) {
    const errorMap = {
      'INSUFFICIENT_BALANCE': 'Insufficient balance in your account',
      'TRANSACTION_LIMIT_EXCEEDED': 'Transaction amount exceeds daily limit',
      'INVALID_VPA': 'Invalid UPI ID or VPA',
      'PAYMENT_DECLINED': 'Payment was declined by your bank',
      'UPI_TIMEOUT': 'Payment timed out, please try again',
      'PAYMENT_CANCELLED': 'Payment was cancelled'
    };

    return errorMap[errorCode] || errorDescription || 'Payment failed. Please try again.';
  }
}

export const upiService = new UPIService();