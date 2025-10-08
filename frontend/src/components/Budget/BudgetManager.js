import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { budgetService } from '../../services/budgetService';

const BudgetManager = () => {
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [formData, setFormData] = useState({
    category: '',
    amount: '',
    period: 'monthly',
  });

  const categories = [
    'Food & Dining',
    'Transportation',
    'Shopping',
    'Entertainment',
    'Bills & Utilities',
    'Healthcare',
    'Other'
  ];

  const periods = [
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'yearly', label: 'Yearly' },
  ];

  useEffect(() => {
    loadBudgets();
  }, []);

  const loadBudgets = async () => {
    try {
      setLoading(true);
      const data = await budgetService.getBudgets();
      // Handle the response structure in case API returns { budgets: [...] } or just [...]
      if (data && Array.isArray(data.budgets)) {
        setBudgets(data.budgets);
      } else if (Array.isArray(data)) {
        setBudgets(data);
      } else {
        setBudgets([]);
      }
    } catch (err) {
      setError('Failed to load budgets');
      setBudgets([]); // Ensure budgets is always an array
      console.error('Error loading budgets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddBudget = () => {
    setEditingBudget(null);
    setFormData({
      category: '',
      amount: '',
      period: 'monthly',
    });
    setOpenDialog(true);
  };

  const handleEditBudget = (budget) => {
    setEditingBudget(budget);
    setFormData({
      category: budget.category || '',
      amount: budget.amount || '',
      period: budget.period || 'monthly',
    });
    setOpenDialog(true);
  };

  const handleSaveBudget = async () => {
    try {
      // Map frontend fields to backend expected fields
      const budgetData = {
        name: editingBudget ? editingBudget.name : `${formData.category} Budget`, // Keep existing name or generate new one
        category: formData.category,
        amount: parseFloat(formData.amount),
        period: formData.period,
      };

      if (editingBudget) {
        await budgetService.updateBudget(editingBudget.id, budgetData);
      } else {
        await budgetService.createBudget(budgetData);
      }
      setOpenDialog(false);
      loadBudgets();
    } catch (err) {
      setError('Failed to save budget');
    }
  };

  const handleDeleteBudget = async (id) => {
    if (window.confirm('Are you sure you want to delete this budget?')) {
      try {
        await budgetService.deleteBudget(id);
        loadBudgets();
      } catch (err) {
        setError('Failed to delete budget');
      }
    }
  };

  const calculateProgress = (spent, budgeted) => {
    if (!budgeted || budgeted === 0) return 0;
    const progress = (spent / budgeted) * 100;
    return Math.max(0, Math.min(progress, 100)); // Ensure value is between 0-100
  };

  const getProgressColor = (progress) => {
    if (progress < 70) return 'success';
    if (progress < 90) return 'warning';
    return 'error';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(amount);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Budget Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddBudget}
        >
          Add Budget
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!Array.isArray(budgets) || budgets.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            No budgets created yet
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Create your first budget to start tracking your spending
          </Typography>
          <Button variant="contained" onClick={handleAddBudget}>
            Create Budget
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {budgets.map((budget) => {
            const spentAmount = budget.spent_amount || 0;
            const budgetAmount = budget.amount || 0;
            const progress = calculateProgress(spentAmount, budgetAmount);
            const remaining = Math.max(budgetAmount - spentAmount, 0);
            
            // Debug logging
            console.log('Budget Debug:', {
              name: budget.name || budget.category,
              spentAmount,
              budgetAmount,
              progress,
              remaining
            });
            
            return (
              <Grid item xs={12} sm={6} md={4} key={budget.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Typography variant="h6" component="h3">
                        {budget.category}
                      </Typography>
                      <Chip
                        label={budget.period}
                        size="small"
                        variant="outlined"
                      />
                    </Box>

                    <Box mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2" color="textSecondary">
                          Spent: {formatCurrency(spentAmount)}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Budget: {formatCurrency(budgetAmount)}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={progress}
                        color={getProgressColor(progress)}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
                        {progress.toFixed(1)}% used
                      </Typography>
                    </Box>

                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Remaining
                        </Typography>
                        <Typography variant="h6" color={remaining > 0 ? 'success.main' : 'error.main'}>
                          {formatCurrency(remaining)}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center">
                        {progress > 100 ? (
                          <TrendingUpIcon color="error" />
                        ) : (
                          <TrendingDownIcon color="success" />
                        )}
                      </Box>
                    </Box>

                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<EditIcon />}
                        onClick={() => handleEditBudget(budget)}
                        sx={{ flex: 1 }}
                      >
                        Edit
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={() => handleDeleteBudget(budget.id)}
                        sx={{ flex: 1 }}
                      >
                        Delete
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Add/Edit Budget Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingBudget ? 'Edit Budget' : 'Add Budget'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Category</InputLabel>
              <Select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                label="Category"
              >
                {categories.map((category) => (
                  <MenuItem key={category} value={category}>
                    {category}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Budget Amount"
              type="number"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              margin="normal"
              InputProps={{
                startAdornment: '₹',
              }}
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Period</InputLabel>
              <Select
                value={formData.period}
                onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                label="Period"
              >
                {periods.map((period) => (
                  <MenuItem key={period.value} value={period.value}>
                    {period.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveBudget} variant="contained">
            {editingBudget ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BudgetManager;