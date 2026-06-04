import pandas as pd
import numpy as np
from src.pipeline.db_client import InfluxDBWrapper
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataPreprocessor:
    def __init__(self):
        self.db_client = InfluxDBWrapper()

    def fetch_raw_data(self, minutes_back: int = 1440) -> pd.DataFrame:
        """Fetches data from InfluxDB and returns a Pandas DataFrame."""
        logger.info(f"Fetching data for the last {minutes_back} minutes...")
        raw_data = self.db_client.query_recent_data(minutes_back)
        if not raw_data:
            logger.warning("No data found for the given timeframe.")
            return pd.DataFrame()
            
        df = pd.DataFrame(raw_data)
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        # Ensure correct types
        df['ppm'] = pd.to_numeric(df['ppm'], errors='coerce')
        df['voltage'] = pd.to_numeric(df['voltage'], errors='coerce')
        return df.sort_index()

    def clean_and_smooth(self, df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
        """
        Applies cleaning techniques:
        1. Drop nulls.
        2. Apply Simple Moving Average (SMA) filter to smooth noisy MQ-135 readings.
        """
        if df.empty:
            return df
            
        # Drop rows with NaN values in crucial columns
        df_cleaned = df.dropna(subset=['ppm']).copy()
        
        # Apply moving average filter to ppm
        df_cleaned['ppm_smoothed'] = df_cleaned['ppm'].rolling(window=window_size, min_periods=1).mean()
        
        return df_cleaned

    def create_lstm_sequences(self, df: pd.DataFrame, time_steps: int = 10, feature_col: str = 'ppm_smoothed'):
        """
        Converts the time-series dataframe into X and y sequences for an LSTM model.
        Returns numpy arrays.
        """
        if df.empty or len(df) <= time_steps:
            logger.error("Not enough data to create sequences.")
            return np.array([]), np.array([])
            
        data = df[feature_col].values
        X, y = [], []
        
        for i in range(len(data) - time_steps):
            X.append(data[i:(i + time_steps)])
            y.append(data[i + time_steps])
            
        # Reshape X to [samples, time_steps, features] expected by LSTM
        X_arr = np.array(X).reshape(-1, time_steps, 1)
        y_arr = np.array(y)
        
        return X_arr, y_arr
