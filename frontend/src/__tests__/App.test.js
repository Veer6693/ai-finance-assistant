import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import Login from '../components/Auth/Login';
import Register from '../components/Auth/Register';
import Dashboard from '../components/Dashboard';
import { authService } from '../services/authService';
import { apiService } from '../services/apiService';

// Mock services
jest.mock('../services/authService');
jest.mock('../services/apiService');

const theme = createTheme();

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Authentication Components', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Login Component', () => {
    test('renders login form', () => {
      renderWithProviders(<Login onLogin={() => {}} />);
      
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    test('handles form submission', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ email: 'test@example.com' });
      authService.login = mockLogin;
      
      const onLogin = jest.fn();
      renderWithProviders(<Login onLogin={onLogin} />);
      
      fireEvent.change(screen.getByLabelText(/email address/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'password123' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
      });
    });

    test('displays error for invalid credentials', async () => {
      const mockLogin = jest.fn().mockRejectedValue(new Error('Invalid credentials'));
      authService.login = mockLogin;
      
      renderWithProviders(<Login onLogin={() => {}} />);
      
      fireEvent.change(screen.getByLabelText(/email address/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'wrongpassword' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
      
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    test('validates empty fields', async () => {
      renderWithProviders(<Login onLogin={() => {}} />);
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
      
      await waitFor(() => {
        expect(screen.getByText(/please fill in all fields/i)).toBeInTheDocument();
      });
    });
  });

  describe('Register Component', () => {
    test('renders registration form', () => {
      renderWithProviders(<Register onLogin={() => {}} />);
      
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    test('validates password confirmation', async () => {
      renderWithProviders(<Register onLogin={() => {}} />);
      
      fireEvent.change(screen.getByLabelText(/full name/i), {
        target: { value: 'Test User' }
      });
      fireEvent.change(screen.getByLabelText(/email address/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' }
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'differentpassword' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      
      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
      });
    });

    test('handles successful registration', async () => {
      const mockRegister = jest.fn().mockResolvedValue({ email: 'test@example.com' });
      authService.register = mockRegister;
      
      const onLogin = jest.fn();
      renderWithProviders(<Register onLogin={onLogin} />);
      
      fireEvent.change(screen.getByLabelText(/full name/i), {
        target: { value: 'Test User' }
      });
      fireEvent.change(screen.getByLabelText(/email address/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' }
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      
      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalled();
      });
    });
  });
});

describe('Dashboard Component', () => {
  const mockUser = {
    id: 1,
    email: 'test@example.com',
    full_name: 'Test User'
  };

  const mockDashboardData = {
    transactions: [],
    spendingAnalysis: {
      total_spending: 15000,
      total_income: 50000,
      category_spending: {
        food: 5000,
        transport: 3000,
        entertainment: 2000
      }
    },
    monthlyTrends: {
      trend: 'increasing',
      monthly_totals: {
        '2024-01': 12000,
        '2024-02': 13000,
        '2024-03': 15000
      }
    },
    budgetPerformance: [
      {
        category: 'food',
        allocated: 8000,
        actual: 5000,
        utilization: 62.5
      }
    ],
    insights: {
      patterns: ['You spend more on weekends'],
      recommendations: ['Consider cooking at home more often'],
      alerts: []
    },
    anomalies: []
  };

  beforeEach(() => {
    jest.clearAllMocks();
    apiService.getDashboardData = jest.fn().mockResolvedValue(mockDashboardData);
  });

  test('renders dashboard with user greeting', async () => {
    renderWithProviders(<Dashboard user={mockUser} />);
    
    await waitFor(() => {
      expect(screen.getByText(/welcome back, test user!/i)).toBeInTheDocument();
    });
  });

  test('displays spending summary cards', async () => {
    renderWithProviders(<Dashboard user={mockUser} />);
    
    await waitFor(() => {
      expect(screen.getByText(/total spending/i)).toBeInTheDocument();
      expect(screen.getByText(/monthly income/i)).toBeInTheDocument();
      expect(screen.getByText(/savings rate/i)).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    apiService.getDashboardData = jest.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 1000))
    );
    
    renderWithProviders(<Dashboard user={mockUser} />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    apiService.getDashboardData = jest.fn().mockRejectedValue(new Error('API Error'));
    
    renderWithProviders(<Dashboard user={mockUser} />);
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
    });
  });

  test('refreshes data on refresh button click', async () => {
    renderWithProviders(<Dashboard user={mockUser} />);
    
    await waitFor(() => {
      expect(screen.getByText(/welcome back, test user!/i)).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);
    
    expect(apiService.getDashboardData).toHaveBeenCalledTimes(2);
  });

  test('displays charts when data is available', async () => {
    renderWithProviders(<Dashboard user={mockUser} />);
    
    await waitFor(() => {
      expect(screen.getByText(/spending trends/i)).toBeInTheDocument();
      expect(screen.getByText(/category breakdown/i)).toBeInTheDocument();
      expect(screen.getByText(/budget performance/i)).toBeInTheDocument();
    });
  });

  test('displays AI insights', async () => {
    renderWithProviders(<Dashboard user={mockUser} />);
    
    await waitFor(() => {
      expect(screen.getByText(/ai insights/i)).toBeInTheDocument();
      expect(screen.getByText(/you spend more on weekends/i)).toBeInTheDocument();
      expect(screen.getByText(/consider cooking at home more often/i)).toBeInTheDocument();
    });
  });
});

describe('Utility Functions', () => {
  test('formatCurrency function', () => {
    const { formatCurrency } = require('../utils/helpers');
    
    expect(formatCurrency(1000)).toBe('₹1,000');
    expect(formatCurrency(50000)).toBe('₹50,000');
    expect(formatCurrency(0)).toBe('₹0');
  });

  test('formatDate function', () => {
    const { formatDate } = require('../utils/helpers');
    
    const testDate = new Date('2024-01-15');
    expect(formatDate(testDate, 'short')).toContain('Jan');
    expect(formatDate(testDate, 'short')).toContain('2024');
  });

  test('validateEmail function', () => {
    const { validateEmail } = require('../utils/helpers');
    
    expect(validateEmail('test@example.com')).toBe(true);
    expect(validateEmail('invalid-email')).toBe(false);
    expect(validateEmail('')).toBe(false);
  });

  test('validatePhone function', () => {
    const { validatePhone } = require('../utils/helpers');
    
    expect(validatePhone('9876543210')).toBe(true);
    expect(validatePhone('1234567890')).toBe(false); // Should start with 6-9
    expect(validatePhone('98765')).toBe(false); // Too short
  });
});

describe('Service Functions', () => {
  describe('AuthService', () => {
    test('stores token on successful login', async () => {
      const mockResponse = {
        data: {
          access_token: 'test_token',
          user: { email: 'test@example.com' }
        }
      };
      
      // Mock axios
      require('axios').post = jest.fn().mockResolvedValue(mockResponse);
      
      const result = await authService.login('test@example.com', 'password');
      
      expect(localStorage.getItem('token')).toBe('test_token');
      expect(result.email).toBe('test@example.com');
    });

    test('removes token on logout', () => {
      localStorage.setItem('token', 'test_token');
      
      authService.logout();
      
      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  describe('ApiService', () => {
    test('includes auth token in requests', () => {
      localStorage.setItem('token', 'test_token');
      
      // Mock axios request interceptor
      const mockRequest = { headers: {} };
      const interceptor = require('axios').interceptors.request.use.mock.calls[0][0];
      
      const result = interceptor(mockRequest);
      
      expect(result.headers.Authorization).toBe('Bearer test_token');
    });
  });
});