import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Payment as PaymentIcon,
  AccountBalance as UPIIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ContentCopy as CopyIcon,
  QrCode as QRIcon,
} from '@mui/icons-material';
import toast from 'react-hot-toast';

import { apiService } from '../../services/apiService';
import { formatCurrency } from '../../utils/helpers';

const UPIPayment = ({ onPaymentComplete }) => {
  const [paymentData, setPaymentData] = useState({
    amount: '',
    vpa: '',
    description: '',
    merchant_name: 'FinanceAI'
  });
  const [mockAccounts, setMockAccounts] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState('');

  useEffect(() => {
    loadMockAccounts();
    loadProviders();
  }, []);

  const loadMockAccounts = async () => {
    try {
      const response = await apiService.get('/upi/mock-accounts');
      if (response.data.success) {
        setMockAccounts(response.data.data.accounts);
      }
    } catch (error) {
      console.error('Failed to load mock accounts:', error);
    }
  };

  const loadProviders = async () => {
    try {
      const response = await apiService.get('/upi/providers');
      if (response.data.success) {
        setProviders(response.data.data.providers);
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setPaymentData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAccountSelect = (account) => {
    setSelectedAccount(account.vpa);
    setPaymentData(prev => ({
      ...prev,
      vpa: account.vpa
    }));
  };

  const validateForm = () => {
    if (!paymentData.amount || parseFloat(paymentData.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return false;
    }
    if (!paymentData.vpa) {
      toast.error('Please select or enter a VPA');
      return false;
    }
    if (!paymentData.description.trim()) {
      toast.error('Please enter a description');
      return false;
    }
    return true;
  };

  const handlePayment = async () => {
    if (!validateForm()) return;

    try {
      setLoading(true);

      const response = await apiService.post('/upi/create-payment', {
        amount: parseFloat(paymentData.amount),
        vpa: paymentData.vpa,
        description: paymentData.description,
        merchant_name: paymentData.merchant_name
      });

      if (response.data.success) {
        const paymentInfo = response.data.data;
        setPaymentStatus({
          ...paymentInfo,
          type: 'success'
        });
        setShowStatusDialog(true);
        
        // Start polling for payment status
        pollPaymentStatus(paymentInfo.payment_id);
        
        toast.success('Payment initiated successfully!');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Payment failed');
      setPaymentStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Payment failed'
      });
      setShowStatusDialog(true);
    } finally {
      setLoading(false);
    }
  };

  const pollPaymentStatus = async (paymentId) => {
    const maxAttempts = 30; // Poll for 30 seconds
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await apiService.get(`/upi/payment-status/${paymentId}`);
        if (response.data.success) {
          const status = response.data.data.status;
          
          setPaymentStatus(prev => ({
            ...prev,
            ...response.data.data,
            type: status === 'captured' ? 'success' : status === 'failed' ? 'error' : 'pending'
          }));

          if (status === 'captured') {
            toast.success('Payment completed successfully!');
            if (onPaymentComplete) {
              onPaymentComplete(response.data.data);
            }
            return;
          } else if (status === 'failed') {
            toast.error('Payment failed: ' + response.data.data.error_description);
            return;
          }
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // Poll every second
        }
      } catch (error) {
        console.error('Error polling payment status:', error);
      }
    };

    poll();
  };

  const handleCloseDialog = () => {
    setShowStatusDialog(false);
    setPaymentStatus(null);
    // Reset form
    setPaymentData({
      amount: '',
      vpa: '',
      description: '',
      merchant_name: 'FinanceAI'
    });
    setSelectedAccount('');
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'captured':
        return <SuccessIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'captured':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'warning';
    }
  };

  return (
    <Box>
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" mb={3}>
            <UPIIcon sx={{ mr: 2, fontSize: 32, color: '#667eea' }} />
            <Typography variant="h5" fontWeight="bold">
              UPI Payment
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {/* Amount Input */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={paymentData.amount}
                onChange={(e) => handleInputChange('amount', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                disabled={loading}
              />
            </Grid>

            {/* Description */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Description"
                value={paymentData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                disabled={loading}
              />
            </Grid>

            {/* VPA Input */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="UPI ID / VPA"
                value={paymentData.vpa}
                onChange={(e) => handleInputChange('vpa', e.target.value)}
                placeholder="example@paytm"
                disabled={loading}
                helperText="Enter recipient's UPI ID or select from test accounts below"
              />
            </Grid>

            {/* Mock Accounts for Testing */}
            {mockAccounts.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Test Accounts (Demo)
                </Typography>
                <Grid container spacing={2}>
                  {mockAccounts.map((account, index) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Card 
                        variant="outlined" 
                        sx={{ 
                          cursor: 'pointer',
                          border: selectedAccount === account.vpa ? '2px solid #667eea' : '1px solid #e0e0e0',
                          '&:hover': { borderColor: '#667eea' }
                        }}
                        onClick={() => handleAccountSelect(account)}
                      >
                        <CardContent sx={{ p: 2 }}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {account.account_holder_name}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            {account.vpa}
                          </Typography>
                          <Box display="flex" justifyContent="space-between" alignItems="center" mt={1}>
                            <Chip 
                              label={account.provider.toUpperCase()} 
                              size="small" 
                              color="primary" 
                            />
                            <Typography variant="body2" fontWeight="bold">
                              {formatCurrency(account.balance)}
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Grid>
            )}

            {/* Payment Button */}
            <Grid item xs={12}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handlePayment}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <PaymentIcon />}
                sx={{
                  height: 56,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                  },
                }}
              >
                {loading ? 'Processing Payment...' : `Pay ${formatCurrency(paymentData.amount || 0)}`}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Payment Status Dialog */}
      <Dialog open={showStatusDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center">
            {paymentStatus && getStatusIcon(paymentStatus.status)}
            <Typography variant="h6" ml={1}>
              Payment Status
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {paymentStatus && (
            <Box>
              <Alert 
                severity={getStatusColor(paymentStatus.status)} 
                sx={{ mb: 2 }}
              >
                {paymentStatus.status === 'captured' && 'Payment completed successfully!'}
                {paymentStatus.status === 'failed' && `Payment failed: ${paymentStatus.error_description}`}
                {paymentStatus.status === 'pending' && 'Payment is being processed...'}
                {paymentStatus.status === 'created' && 'Payment initiated, waiting for completion...'}
              </Alert>

              <List>
                {paymentStatus.payment_id && (
                  <ListItem>
                    <ListItemText 
                      primary="Payment ID" 
                      secondary={
                        <Box display="flex" alignItems="center">
                          <Typography variant="body2">{paymentStatus.payment_id}</Typography>
                          <IconButton 
                            size="small" 
                            onClick={() => copyToClipboard(paymentStatus.payment_id)}
                          >
                            <CopyIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      } 
                    />
                  </ListItem>
                )}
                
                {paymentStatus.amount && (
                  <ListItem>
                    <ListItemText 
                      primary="Amount" 
                      secondary={formatCurrency(paymentStatus.amount)} 
                    />
                  </ListItem>
                )}
                
                {paymentStatus.vpa && (
                  <ListItem>
                    <ListItemText 
                      primary="Recipient VPA" 
                      secondary={paymentStatus.vpa} 
                    />
                  </ListItem>
                )}
                
                {paymentStatus.provider && (
                  <ListItem>
                    <ListItemText 
                      primary="Provider" 
                      secondary={paymentStatus.provider.toUpperCase()} 
                    />
                  </ListItem>
                )}
              </List>

              {paymentStatus.status === 'pending' && (
                <Box display="flex" justifyContent="center" mt={2}>
                  <CircularProgress />
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>
            {paymentStatus?.status === 'captured' || paymentStatus?.status === 'failed' ? 'Close' : 'Cancel'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UPIPayment;