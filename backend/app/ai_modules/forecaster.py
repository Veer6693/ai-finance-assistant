import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import logging
import json

logger = logging.getLogger(__name__)

class SpendingForecaster:
    """
    LSTM-based time series forecasting for spending prediction and trend analysis.
    Predicts future spending patterns and identifies anomalies in user behavior.
    """
    
    def __init__(self, sequence_length: int = 30, model_path: str = "trained_models/forecaster"):
        self.sequence_length = sequence_length  # Number of days to look back
        self.model_path = model_path
        
        # Model components
        self.lstm_model = None
        self.amount_scaler = MinMaxScaler()
        self.feature_scaler = StandardScaler()
        
        # Model parameters
        self.lstm_units = [64, 32]
        self.dropout_rate = 0.2
        self.learning_rate = 0.001
        self.batch_size = 32
        self.epochs = 100
        
        # Categories for multi-target prediction
        self.categories = [
            "food", "groceries", "transport", "shopping", "entertainment",
            "bills", "healthcare", "investment", "education", "other"
        ]
        
        # Performance tracking
        self.training_history = {}
        self.model_metrics = {}
    
    def prepare_data(self, transactions: List[Dict]) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        Prepare transaction data for LSTM training.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Tuple of (X, y, daily_aggregated_data)
        """
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Filter out credit transactions for spending analysis
        spending_df = df[df['transaction_type'] == 'debit'].copy()
        
        # Create daily aggregated data
        daily_data = self._create_daily_aggregation(spending_df)
        
        # Create sequences for LSTM
        X, y = self._create_sequences(daily_data)
        
        return X, y, daily_data
    
    def _create_daily_aggregation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create daily aggregated spending data with features.
        """
        # Ensure we have a complete date range
        date_range = pd.date_range(
            start=df['transaction_date'].min().date(),
            end=df['transaction_date'].max().date(),
            freq='D'
        )
        
        # Aggregate by date and category
        daily_category = df.groupby([
            df['transaction_date'].dt.date,
            'ai_category'
        ])['amount'].sum().unstack(fill_value=0)
        
        # Ensure all categories are present
        for category in self.categories:
            if category not in daily_category.columns:
                daily_category[category] = 0
        
        # Create daily totals
        daily_totals = df.groupby(df['transaction_date'].dt.date).agg({
            'amount': ['sum', 'count', 'mean', 'std'],
            'ai_category': lambda x: len(set(x))  # Number of unique categories
        }).round(2)
        
        daily_totals.columns = ['total_amount', 'transaction_count', 'avg_amount', 'std_amount', 'unique_categories']
        
        # Combine data
        daily_data = pd.DataFrame(index=date_range)
        daily_data.index.name = 'date'
        
        # Add category spending
        for category in self.categories:
            daily_data[f'{category}_spending'] = daily_category.get(category, 0)
        
        # Add aggregate features
        for col in daily_totals.columns:
            daily_data[col] = daily_totals[col] if col in daily_totals else 0
        
        # Fill missing values
        daily_data = daily_data.fillna(0)
        
        # Add temporal features
        daily_data['day_of_week'] = daily_data.index.dayofweek
        daily_data['day_of_month'] = daily_data.index.day
        daily_data['month'] = daily_data.index.month
        daily_data['is_weekend'] = (daily_data['day_of_week'] >= 5).astype(int)
        daily_data['is_month_start'] = (daily_data['day_of_month'] <= 5).astype(int)
        daily_data['is_month_end'] = (daily_data['day_of_month'] >= 25).astype(int)
        
        # Add rolling averages
        for window in [7, 14, 30]:
            daily_data[f'total_amount_ma_{window}'] = daily_data['total_amount'].rolling(window=window, min_periods=1).mean()
            daily_data[f'transaction_count_ma_{window}'] = daily_data['transaction_count'].rolling(window=window, min_periods=1).mean()
        
        # Add lag features
        for lag in [1, 7, 30]:
            daily_data[f'total_amount_lag_{lag}'] = daily_data['total_amount'].shift(lag)
        
        # Fill NaN values created by lag and rolling operations
        daily_data = daily_data.fillna(method='bfill').fillna(0)
        
        return daily_data
    
    def _create_sequences(self, daily_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create input sequences and targets for LSTM.
        """
        # Features for input
        feature_columns = [
            'total_amount', 'transaction_count', 'avg_amount', 'unique_categories',
            'day_of_week', 'is_weekend', 'is_month_start', 'is_month_end'
        ]
        
        # Add category spending features
        feature_columns.extend([f'{cat}_spending' for cat in self.categories])
        
        # Add rolling averages
        feature_columns.extend([f'total_amount_ma_{w}' for w in [7, 14, 30]])
        
        # Add lag features
        feature_columns.extend([f'total_amount_lag_{lag}' for lag in [1, 7, 30]])
        
        # Target columns (what we want to predict)
        target_columns = ['total_amount'] + [f'{cat}_spending' for cat in self.categories]
        
        # Scale features
        features = daily_data[feature_columns].values
        targets = daily_data[target_columns].values
        
        features_scaled = self.feature_scaler.fit_transform(features)
        targets_scaled = self.amount_scaler.fit_transform(targets)
        
        # Create sequences
        X, y = [], []
        
        for i in range(self.sequence_length, len(features_scaled)):
            X.append(features_scaled[i-self.sequence_length:i])
            y.append(targets_scaled[i])
        
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape: Tuple, output_shape: int) -> tf.keras.Model:
        """
        Build LSTM model architecture.
        """
        model = Sequential([
            # First LSTM layer
            LSTM(
                self.lstm_units[0],
                return_sequences=True,
                input_shape=input_shape,
                dropout=self.dropout_rate,
                recurrent_dropout=self.dropout_rate
            ),
            BatchNormalization(),
            
            # Second LSTM layer
            LSTM(
                self.lstm_units[1],
                return_sequences=False,
                dropout=self.dropout_rate,
                recurrent_dropout=self.dropout_rate
            ),
            BatchNormalization(),
            
            # Dense layers
            Dense(32, activation='relu'),
            Dropout(self.dropout_rate),
            Dense(16, activation='relu'),
            Dropout(self.dropout_rate),
            
            # Output layer
            Dense(output_shape, activation='linear')
        ])
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        return model
    
    def train(self, transactions: List[Dict], validation_split: float = 0.2) -> Dict:
        """
        Train the LSTM model on transaction data.
        
        Args:
            transactions: List of transaction dictionaries
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training metrics and history
        """
        logger.info(f"Training forecasting model with {len(transactions)} transactions")
        
        # Prepare data
        X, y, daily_data = self.prepare_data(transactions)
        
        if len(X) < self.sequence_length * 2:
            raise ValueError(f"Not enough data for training. Need at least {self.sequence_length * 2} days of data.")
        
        # Build model
        self.lstm_model = self.build_model(
            input_shape=(X.shape[1], X.shape[2]),
            output_shape=y.shape[1]
        )
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=8,
                min_lr=1e-7
            )
        ]
        
        # Train model
        history = self.lstm_model.fit(
            X, y,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        # Store training history
        self.training_history = history.history
        
        # Calculate metrics
        train_predictions = self.lstm_model.predict(X)
        train_predictions_inverse = self.amount_scaler.inverse_transform(train_predictions)
        y_inverse = self.amount_scaler.inverse_transform(y)
        
        # Calculate errors for total spending (first column)
        mae = mean_absolute_error(y_inverse[:, 0], train_predictions_inverse[:, 0])
        mse = mean_squared_error(y_inverse[:, 0], train_predictions_inverse[:, 0])
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_inverse[:, 0] - train_predictions_inverse[:, 0]) / np.maximum(y_inverse[:, 0], 1))) * 100
        
        self.model_metrics = {
            "mae": float(mae),
            "mse": float(mse),
            "rmse": float(rmse),
            "mape": float(mape),
            "training_samples": len(X),
            "sequence_length": self.sequence_length,
            "model_architecture": {
                "lstm_units": self.lstm_units,
                "dropout_rate": self.dropout_rate,
                "learning_rate": self.learning_rate
            }
        }
        
        # Save model
        self.save_model()
        
        logger.info(f"Model trained successfully. RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")
        return self.model_metrics
    
    def predict_future_spending(self, 
                              recent_data: pd.DataFrame, 
                              days_ahead: int = 30) -> Dict:
        """
        Predict future spending for the next N days.
        
        Args:
            recent_data: Recent daily aggregated data
            days_ahead: Number of days to predict
            
        Returns:
            Dictionary with predictions
        """
        if self.lstm_model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = []
        current_sequence = recent_data.tail(self.sequence_length)
        
        # Feature columns (same as training)
        feature_columns = [
            'total_amount', 'transaction_count', 'avg_amount', 'unique_categories',
            'day_of_week', 'is_weekend', 'is_month_start', 'is_month_end'
        ]
        feature_columns.extend([f'{cat}_spending' for cat in self.categories])
        feature_columns.extend([f'total_amount_ma_{w}' for w in [7, 14, 30]])
        feature_columns.extend([f'total_amount_lag_{lag}' for lag in [1, 7, 30]])
        
        for day in range(days_ahead):
            # Prepare input sequence
            input_features = current_sequence[feature_columns].values
            input_scaled = self.feature_scaler.transform(input_features)
            input_sequence = input_scaled.reshape(1, self.sequence_length, -1)
            
            # Make prediction
            prediction_scaled = self.lstm_model.predict(input_sequence, verbose=0)
            prediction = self.amount_scaler.inverse_transform(prediction_scaled)[0]
            
            # Extract total spending and category breakdown
            total_spending = max(0, prediction[0])  # Ensure non-negative
            category_spending = {
                self.categories[i]: max(0, prediction[i+1]) 
                for i in range(len(self.categories))
            }
            
            # Create prediction date
            prediction_date = current_sequence.index[-1] + timedelta(days=day+1)
            
            prediction_dict = {
                "date": prediction_date.strftime("%Y-%m-%d"),
                "total_spending": round(total_spending, 2),
                "category_breakdown": {k: round(v, 2) for k, v in category_spending.items()},
                "confidence": self._calculate_prediction_confidence(day)
            }
            
            predictions.append(prediction_dict)
            
            # Update sequence for next prediction (simplified)
            # In practice, you'd want to create proper features for the predicted day
            next_row = self._create_next_day_features(prediction_date, prediction)
            current_sequence = pd.concat([current_sequence.iloc[1:], next_row])
        
        return {
            "predictions": predictions,
            "total_predicted_spending": sum(p["total_spending"] for p in predictions),
            "prediction_period": f"{days_ahead} days",
            "model_accuracy": self.model_metrics.get("mape", "Unknown")
        }
    
    def _create_next_day_features(self, date: datetime, prediction: np.ndarray) -> pd.DataFrame:
        """Create features for the next day based on prediction"""
        # This is a simplified version - in practice, you'd want more sophisticated feature engineering
        next_day_data = {
            'total_amount': max(0, prediction[0]),
            'transaction_count': 5,  # Estimated average
            'avg_amount': max(0, prediction[0]) / 5,
            'unique_categories': len([x for x in prediction[1:] if x > 0]),
            'day_of_week': date.weekday(),
            'is_weekend': 1 if date.weekday() >= 5 else 0,
            'is_month_start': 1 if date.day <= 5 else 0,
            'is_month_end': 1 if date.day >= 25 else 0
        }
        
        # Add category spending
        for i, category in enumerate(self.categories):
            next_day_data[f'{category}_spending'] = max(0, prediction[i+1])
        
        # Add placeholder values for rolling averages and lags
        for window in [7, 14, 30]:
            next_day_data[f'total_amount_ma_{window}'] = max(0, prediction[0])
        
        for lag in [1, 7, 30]:
            next_day_data[f'total_amount_lag_{lag}'] = max(0, prediction[0])
        
        return pd.DataFrame([next_day_data], index=[date])
    
    def _calculate_prediction_confidence(self, days_ahead: int) -> float:
        """Calculate confidence score for prediction based on days ahead"""
        # Confidence decreases as we predict further into the future
        base_confidence = 0.9
        decay_rate = 0.02
        return max(0.1, base_confidence * np.exp(-decay_rate * days_ahead))
    
    def detect_anomalies(self, 
                        daily_data: pd.DataFrame, 
                        threshold_std: float = 2.5) -> Dict:
        """
        Detect spending anomalies using statistical methods and model predictions.
        
        Args:
            daily_data: Daily aggregated spending data
            threshold_std: Number of standard deviations for anomaly detection
            
        Returns:
            Dictionary with anomaly information
        """
        anomalies = []
        
        # Statistical anomaly detection
        spending_mean = daily_data['total_amount'].mean()
        spending_std = daily_data['total_amount'].std()
        threshold = spending_mean + threshold_std * spending_std
        
        statistical_anomalies = daily_data[daily_data['total_amount'] > threshold]
        
        for date, row in statistical_anomalies.iterrows():
            anomalies.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": row['total_amount'],
                "type": "statistical",
                "severity": "high" if row['total_amount'] > threshold * 1.5 else "medium",
                "description": f"Spending of ₹{row['total_amount']:.2f} is {((row['total_amount'] - spending_mean) / spending_std):.1f} standard deviations above average"
            })
        
        # Model-based anomaly detection (if model is trained)
        if self.lstm_model is not None and len(daily_data) > self.sequence_length:
            # Compare actual vs predicted for recent data
            X, y = self._create_sequences(daily_data)
            if len(X) > 0:
                predictions = self.lstm_model.predict(X, verbose=0)
                predictions_inverse = self.amount_scaler.inverse_transform(predictions)
                y_inverse = self.amount_scaler.inverse_transform(y)
                
                # Calculate prediction errors
                errors = np.abs(y_inverse[:, 0] - predictions_inverse[:, 0])
                error_threshold = np.percentile(errors, 95)  # Top 5% of errors
                
                model_anomaly_indices = np.where(errors > error_threshold)[0]
                
                for idx in model_anomaly_indices:
                    date = daily_data.index[idx + self.sequence_length]
                    actual = y_inverse[idx, 0]
                    predicted = predictions_inverse[idx, 0]
                    
                    anomalies.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "amount": actual,
                        "predicted_amount": predicted,
                        "type": "model_based",
                        "severity": "high" if abs(actual - predicted) > error_threshold * 2 else "medium",
                        "description": f"Actual spending ₹{actual:.2f} significantly different from predicted ₹{predicted:.2f}"
                    })
        
        return {
            "anomalies": anomalies,
            "total_anomalies": len(anomalies),
            "anomaly_rate": len(anomalies) / len(daily_data) * 100,
            "detection_methods": ["statistical", "model_based"] if self.lstm_model else ["statistical"]
        }
    
    def get_spending_insights(self, daily_data: pd.DataFrame) -> Dict:
        """
        Generate insights about spending patterns.
        """
        insights = {
            "spending_summary": {
                "total_spending": daily_data['total_amount'].sum(),
                "average_daily_spending": daily_data['total_amount'].mean(),
                "highest_spending_day": {
                    "date": daily_data['total_amount'].idxmax().strftime("%Y-%m-%d"),
                    "amount": daily_data['total_amount'].max()
                },
                "lowest_spending_day": {
                    "date": daily_data['total_amount'].idxmin().strftime("%Y-%m-%d"),
                    "amount": daily_data['total_amount'].min()
                }
            },
            "patterns": {
                "weekend_vs_weekday": {
                    "weekend_avg": daily_data[daily_data['is_weekend'] == 1]['total_amount'].mean(),
                    "weekday_avg": daily_data[daily_data['is_weekend'] == 0]['total_amount'].mean()
                },
                "month_start_vs_end": {
                    "month_start_avg": daily_data[daily_data['is_month_start'] == 1]['total_amount'].mean(),
                    "month_end_avg": daily_data[daily_data['is_month_end'] == 1]['total_amount'].mean()
                }
            },
            "trends": {
                "spending_trend": "increasing" if daily_data['total_amount'].corr(range(len(daily_data))) > 0 else "decreasing",
                "correlation_with_time": daily_data['total_amount'].corr(range(len(daily_data)))
            }
        }
        
        return insights
    
    def save_model(self):
        """Save the trained model and scalers"""
        import os
        os.makedirs(self.model_path, exist_ok=True)
        
        if self.lstm_model:
            self.lstm_model.save(f"{self.model_path}/lstm_model.h5")
        
        joblib.dump(self.amount_scaler, f"{self.model_path}/amount_scaler.pkl")
        joblib.dump(self.feature_scaler, f"{self.model_path}/feature_scaler.pkl")
        
        # Save metadata
        metadata = {
            "sequence_length": self.sequence_length,
            "categories": self.categories,
            "model_metrics": self.model_metrics,
            "training_history": self.training_history
        }
        
        with open(f"{self.model_path}/metadata.json", 'w') as f:
            json.dump(metadata, f, default=str)
        
        logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load the trained model and scalers"""
        import os
        
        try:
            if os.path.exists(f"{self.model_path}/lstm_model.h5"):
                self.lstm_model = tf.keras.models.load_model(f"{self.model_path}/lstm_model.h5")
            
            if os.path.exists(f"{self.model_path}/amount_scaler.pkl"):
                self.amount_scaler = joblib.load(f"{self.model_path}/amount_scaler.pkl")
            
            if os.path.exists(f"{self.model_path}/feature_scaler.pkl"):
                self.feature_scaler = joblib.load(f"{self.model_path}/feature_scaler.pkl")
            
            # Load metadata
            if os.path.exists(f"{self.model_path}/metadata.json"):
                with open(f"{self.model_path}/metadata.json", 'r') as f:
                    metadata = json.load(f)
                    self.model_metrics = metadata.get("model_metrics", {})
                    self.training_history = metadata.get("training_history", {})
            
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # This would typically be called with real transaction data
    print("SpendingForecaster initialized. Use with real transaction data for training and prediction.")