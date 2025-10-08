import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  Chip,
  IconButton,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AccountBalance as AccountBalanceIcon,
  CreditCard as CreditCardIcon,
  Savings as SavingsIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';
import { format, parseISO } from 'date-fns';
import toast from 'react-hot-toast';

import { apiService } from '../services/apiService';
import { authService } from '../services/authService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);

  // Map backend categories to frontend display categories
  const mapBackendCategoryToDisplay = (backendCategory) => {
    const categoryMap = {
      'food': 'Food & Dining',
      'groceries': 'Food & Dining',
      'transport': 'Transportation', 
      'shopping': 'Shopping',
      'entertainment': 'Entertainment',
      'bills': 'Bills & Utilities',
      'healthcare': 'Healthcare',
      'investment': 'Investment',
      'education': 'Other',
      'income': 'Income',
      'other': 'Other'
    };
    
    return categoryMap[backendCategory?.toLowerCase()] || backendCategory || 'Other';
  };

  useEffect(() => {
    loadDashboardData();
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (err) {
      console.error('Failed to load user data:', err);
      // Set a default user object to prevent errors
      setUser({ username: 'User', email: 'user@example.com' });
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getDashboardData();
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getSpendingTrendData = () => {
    if (!dashboardData?.monthlyTrends?.monthly_totals) return null;

    const monthlyData = dashboardData.monthlyTrends.monthly_totals;
    const labels = Object.keys(monthlyData).map(month => {
      try {
        return format(parseISO(month + '-01'), 'MMM yyyy');
      } catch {
        return month;
      }
    });
    const data = Object.values(monthlyData);

    return {
      labels,
      datasets: [
        {
          label: 'Monthly Spending',
          data,
          borderColor: 'rgb(102, 126, 234)',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
        },
      ],
    };
  };

  const getCategorySpendingData = () => {
    if (!dashboardData?.spendingAnalysis?.category_breakdown) return null;

    const categoryData = dashboardData.spendingAnalysis.category_breakdown;
    
    // Map backend categories to display categories and aggregate
    const mappedData = {};
    Object.entries(categoryData).forEach(([backendCategory, amount]) => {
      const displayCategory = mapBackendCategoryToDisplay(backendCategory);
      mappedData[displayCategory] = (mappedData[displayCategory] || 0) + amount;
    });
    
    const labels = Object.keys(mappedData);
    const data = Object.values(mappedData);

    const backgroundColors = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
      '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ];

    return {
      labels,
      datasets: [
        {
          data,
          backgroundColor: backgroundColors.slice(0, labels.length),
          borderWidth: 2,
          borderColor: '#fff',
        },
      ],
    };
  };

  const getBudgetPerformanceData = () => {
    if (!dashboardData?.budgetPerformance || !Array.isArray(dashboardData.budgetPerformance)) return null;

    const budgets = dashboardData.budgetPerformance;
    const labels = budgets.map(b => {
      const name = b.budget_name || b.name || 'Unknown Budget';
      return name.charAt(0).toUpperCase() + name.slice(1);
    });
    const allocated = budgets.map(b => b.allocated_amount || b.allocated || 0);
    const actual = budgets.map(b => b.spent_amount || b.actual || 0);

    return {
      labels,
      datasets: [
        {
          label: 'Allocated',
          data: allocated,
          backgroundColor: 'rgba(102, 126, 234, 0.6)',
          borderColor: 'rgb(102, 126, 234)',
          borderWidth: 1,
        },
        {
          label: 'Actual',
          data: actual,
          backgroundColor: 'rgba(244, 67, 54, 0.6)',
          borderColor: 'rgb(244, 67, 54)',
          borderWidth: 1,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return '₹' + value.toLocaleString();
          }
        }
      }
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = formatCurrency(context.parsed);
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((context.parsed / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    },
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        action={
          <Button color="inherit" size="small" onClick={loadDashboardData}>
            Try Again
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  const totalSpending = dashboardData?.spendingAnalysis?.total_spending || 0;
  const totalIncome = dashboardData?.spendingAnalysis?.total_income || 0;
  const savingsRate = totalIncome > 0 ? ((totalIncome - totalSpending) / totalIncome * 100) : 0;
  const anomaliesCount = dashboardData?.anomalies?.length || 0;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Welcome back, {user?.full_name || user?.username || user?.email || 'User'}!
        </Typography>
        <IconButton onClick={loadDashboardData} disabled={loading}>
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="stat-card">
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" color="inherit">
                    Total Spending
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="inherit">
                    {formatCurrency(totalSpending)}
                  </Typography>
                </Box>
                <CreditCardIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card className="stat-card success">
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" color="inherit">
                    Monthly Income
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="inherit">
                    {formatCurrency(totalIncome)}
                  </Typography>
                </Box>
                <AccountBalanceIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card className={`stat-card ${savingsRate > 20 ? 'success' : savingsRate > 10 ? 'warning' : 'danger'}`}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" color="inherit">
                    Savings Rate
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="inherit">
                    {savingsRate.toFixed(1)}%
                  </Typography>
                </Box>
                <SavingsIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card className={`stat-card ${anomaliesCount > 0 ? 'warning' : 'success'}`}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" color="inherit">
                    Anomalies
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="inherit">
                    {anomaliesCount}
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} mb={4}>
        {/* Spending Trends */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2}>
                Spending Trends
              </Typography>
              <Box height={300}>
                {getSpendingTrendData() ? (
                  <Line data={getSpendingTrendData()} options={chartOptions} />
                ) : (
                  <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                    <Typography color="textSecondary">No trend data available</Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Category Spending */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2}>
                Category Breakdown
              </Typography>
              <Box height={300}>
                {getCategorySpendingData() ? (
                  <Doughnut data={getCategorySpendingData()} options={doughnutOptions} />
                ) : (
                  <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                    <Typography color="textSecondary">No category data available</Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Budget Performance and Insights */}
      <Grid container spacing={3}>
        {/* Budget Performance */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2}>
                Budget Performance
              </Typography>
              <Box height={300}>
                {getBudgetPerformanceData() ? (
                  <Bar data={getBudgetPerformanceData()} options={chartOptions} />
                ) : (
                  <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                    <Typography color="textSecondary">No budget data available</Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* AI Insights */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2}>
                AI Insights
              </Typography>
              <Box>
                {dashboardData?.insights?.patterns?.map((pattern, index) => (
                  <Chip
                    key={index}
                    label={pattern}
                    variant="outlined"
                    sx={{ mb: 1, mr: 1 }}
                    size="small"
                  />
                ))}
                {dashboardData?.insights?.recommendations?.map((rec, index) => (
                  <Alert key={index} severity="info" sx={{ mb: 1 }}>
                    {rec}
                  </Alert>
                ))}
                {dashboardData?.insights?.alerts?.map((alert, index) => (
                  <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                    {alert}
                  </Alert>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;