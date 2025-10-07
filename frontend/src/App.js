import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Toaster } from 'react-hot-toast';

// Components
import Dashboard from './components/Dashboard';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import TransactionList from './components/Transactions/TransactionList';
import BudgetManager from './components/Budget/BudgetManager';
import AIChat from './components/AI/AIChat';
import Profile from './components/Profile/Profile';
import Layout from './components/Layout/Layout';

// Services
import { authService } from './services/authService';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff6584',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#1976d2',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is authenticated on app load
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          // Verify token with backend
          const userData = await authService.verifyToken();
          setUser(userData);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          backgroundColor: '#f5f5f5'
        }}>
          <div>Loading...</div>
        </div>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                theme: {
                  primary: '#4aed88',
                },
              },
            }}
          />
          
          {!isAuthenticated ? (
            <Routes>
              <Route 
                path="/login" 
                element={<Login onLogin={handleLogin} />} 
              />
              <Route 
                path="/register" 
                element={<Register onLogin={handleLogin} />} 
              />
              <Route 
                path="*" 
                element={<Navigate to="/login" replace />} 
              />
            </Routes>
          ) : (
            <Layout user={user} onLogout={handleLogout}>
              <Routes>
                <Route 
                  path="/" 
                  element={<Dashboard user={user} />} 
                />
                <Route 
                  path="/dashboard" 
                  element={<Dashboard user={user} />} 
                />
                <Route 
                  path="/transactions" 
                  element={<TransactionList user={user} />} 
                />
                <Route 
                  path="/budget" 
                  element={<BudgetManager user={user} />} 
                />
                <Route 
                  path="/ai-chat" 
                  element={<AIChat user={user} />} 
                />
                <Route 
                  path="/profile" 
                  element={<Profile user={user} onUpdate={setUser} />} 
                />
                <Route 
                  path="*" 
                  element={<Navigate to="/dashboard" replace />} 
                />
              </Routes>
            </Layout>
          )}
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;