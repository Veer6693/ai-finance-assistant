import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { transactionService } from '../../services/transactionService';

const TransactionList = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    category: '',
    type: 'expense',
  });

  const categories = [
    'Food & Dining',
    'Transportation',
    'Shopping',
    'Entertainment',
    'Bills & Utilities',
    'Healthcare',
    'Investment',
    'Income',
    'Other'
  ];

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const data = await transactionService.getTransactions();
      // Handle the response structure: { transactions: [...], total: n, page: n, ... }
      if (data && Array.isArray(data.transactions)) {
        setTransactions(data.transactions);
      } else if (Array.isArray(data)) {
        // Fallback if API returns array directly
        setTransactions(data);
      } else {
        setTransactions([]);
      }
    } catch (err) {
      setError('Failed to load transactions');
      setTransactions([]); // Ensure transactions is always an array
      console.error('Error loading transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      description: '',
      amount: '',
      category: '',
      type: 'expense',
    });
    setEditingTransaction(null);
  };

  const handleAddTransaction = () => {
    resetForm();
    setOpenDialog(true);
  };

  const handleEditTransaction = (transaction) => {
    setEditingTransaction(transaction);
    setFormData({
      description: transaction.description || '',
      amount: transaction.amount || '',
      category: transaction.ai_category || transaction.merchant_category || '',
      type: transaction.transaction_type === 'credit' ? 'income' : 'expense',
    });
    setOpenDialog(true);
  };

  const handleDeleteTransaction = async (id) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await transactionService.deleteTransaction(id);
        loadTransactions();
      } catch (err) {
        setError('Failed to delete transaction');
      }
    }
  };

  const handleSaveTransaction = async () => {
    try {
      // Map frontend fields to backend expected fields
      const transactionData = {
        amount: parseFloat(formData.amount),
        transaction_type: formData.type === 'expense' ? 'debit' : 'credit',
        description: formData.description,
        merchant_name: formData.description, // Use description as merchant name if not provided
        merchant_category: formData.category,
        transaction_date: new Date().toISOString()
      };

      if (editingTransaction) {
        await transactionService.updateTransaction(editingTransaction.transaction_id, transactionData);
      } else {
        await transactionService.createTransaction(transactionData);
      }
      setOpenDialog(false);
      resetForm();
      loadTransactions();
    } catch (err) {
      console.error('Transaction save error:', err);
      setError('Failed to save transaction');
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Food & Dining': 'primary',
      'Transportation': 'secondary',
      'Shopping': 'error',
      'Entertainment': 'warning',
      'Bills & Utilities': 'info',
      'Healthcare': 'success',
      'Investment': 'primary',
      'Income': 'success',
      'Other': 'default'
    };
    return colors[category] || 'default';
  };

  const formatAmount = (amount, type) => {
    const formatted = new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(Math.abs(amount));
    
    return type === 'income' ? `+${formatted}` : `-${formatted}`;
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
          Transactions
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddTransaction}
        >
          Add Transaction
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Description</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!Array.isArray(transactions) || transactions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="textSecondary">
                    No transactions found. Add your first transaction!
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              transactions.map((transaction) => (
                <TableRow key={transaction.id}>
                  <TableCell>{transaction.description}</TableCell>
                  <TableCell>
                    <Typography
                      color={transaction.transaction_type === 'credit' ? 'success.main' : 'error.main'}
                      fontWeight="medium"
                    >
                      {formatAmount(transaction.amount, transaction.transaction_type === 'credit' ? 'income' : 'expense')}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={transaction.ai_category || transaction.merchant_category || 'Uncategorized'}
                      color={getCategoryColor(transaction.ai_category || transaction.merchant_category)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={transaction.transaction_type === 'credit' ? 'Income' : 'Expense'}
                      variant="outlined"
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(transaction.transaction_date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => handleEditTransaction(transaction)}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteTransaction(transaction.transaction_id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Transaction Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingTransaction ? 'Edit Transaction' : 'Add Transaction'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Amount"
              type="number"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              margin="normal"
            />
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
            <FormControl fullWidth margin="normal">
              <InputLabel>Type</InputLabel>
              <Select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                label="Type"
              >
                <MenuItem value="expense">Expense</MenuItem>
                <MenuItem value="income">Income</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveTransaction} variant="contained">
            {editingTransaction ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TransactionList;