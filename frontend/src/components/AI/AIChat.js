import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { aiService } from '../../services/aiService';

const AIChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! I'm your AI finance assistant. Ask me anything about your spending, budgets, or financial insights!",
      sender: 'bot',
      timestamp: new Date(),
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);
    setError(null);

    try {
      const response = await aiService.processQuery(inputText);
      
      const botMessage = {
        id: Date.now() + 1,
        text: response.answer || 'I apologize, but I cannot process your request right now.',
        sender: 'bot',
        timestamp: new Date(),
        data: response.data,
        intent: response.intent,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to get response from AI assistant');
      
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your request. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
        isError: true,
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderMessageContent = (message) => {
    if (message.data && message.intent) {
      return (
        <Box>
          <Typography variant="body1" sx={{ mb: 1 }}>
            {message.text}
          </Typography>
          
          {message.intent && (
            <Chip 
              label={`Intent: ${message.intent}`} 
              size="small" 
              variant="outlined" 
              sx={{ mb: 1 }}
            />
          )}

          {message.data && typeof message.data === 'object' && (
            <Card variant="outlined" sx={{ mt: 1, maxWidth: 300 }}>
              <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                <Typography variant="caption" color="textSecondary">
                  Data Summary:
                </Typography>
                <pre style={{ 
                  fontSize: '12px', 
                  margin: 0, 
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {JSON.stringify(message.data, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </Box>
      );
    }

    return (
      <Typography variant="body1">
        {message.text}
      </Typography>
    );
  };

  const suggestedQueries = [
    "How much did I spend on food last month?",
    "What's my biggest expense category?",
    "Show me my spending trends",
    "How am I doing with my budget?",
    "What transactions were over ₹1000?",
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Financial Assistant
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
        {/* Messages Area */}
        <Box sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 1,
          backgroundColor: '#f5f5f5'
        }}>
          <List>
            {messages.map((message) => (
              <ListItem 
                key={message.id}
                sx={{
                  flexDirection: 'column',
                  alignItems: message.sender === 'user' ? 'flex-end' : 'flex-start',
                  mb: 1,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                    maxWidth: '80%',
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: message.sender === 'user' ? 'primary.main' : 'secondary.main',
                      mx: 1,
                    }}
                  >
                    {message.sender === 'user' ? <PersonIcon /> : <BotIcon />}
                  </Avatar>
                  
                  <Card
                    sx={{
                      bgcolor: message.sender === 'user' ? 'primary.light' : 'white',
                      color: message.sender === 'user' ? 'white' : 'text.primary',
                      borderRadius: 2,
                      ...(message.isError && { bgcolor: 'error.light' }),
                    }}
                  >
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      {renderMessageContent(message)}
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          display: 'block', 
                          mt: 1, 
                          opacity: 0.7,
                          textAlign: message.sender === 'user' ? 'right' : 'left'
                        }}
                      >
                        {formatTimestamp(message.timestamp)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
              </ListItem>
            ))}
            {loading && (
              <ListItem sx={{ justifyContent: 'flex-start' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
                  <Avatar sx={{ bgcolor: 'secondary.main', mr: 1 }}>
                    <BotIcon />
                  </Avatar>
                  <CircularProgress size={20} />
                  <Typography variant="body2" sx={{ ml: 1 }}>
                    AI is thinking...
                  </Typography>
                </Box>
              </ListItem>
            )}
          </List>
          <div ref={messagesEndRef} />
        </Box>

        <Divider />

        {/* Input Area */}
        <Box sx={{ p: 2, backgroundColor: 'white' }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={3}
              placeholder="Ask me about your finances..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              variant="outlined"
              size="small"
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputText.trim() || loading}
              sx={{ mb: 0.5 }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>

      {/* Suggested Queries */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Try asking:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {suggestedQueries.map((query, index) => (
            <Chip
              key={index}
              label={query}
              variant="outlined"
              clickable
              onClick={() => setInputText(query)}
              size="small"
            />
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export default AIChat;