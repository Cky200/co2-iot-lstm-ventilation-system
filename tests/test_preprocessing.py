import numpy as np
import pandas as pd
import pytest

from src.pipeline.preprocessing import DataPreprocessor


@pytest.fixture
def preprocessor():
    with patch('src.pipeline.preprocessing.InfluxDBWrapper'):
        yield DataPreprocessor()

from unittest.mock import patch


def test_fetch_raw_data_empty():
    with patch('src.pipeline.preprocessing.InfluxDBWrapper') as MockDB:
        mock_instance = MockDB.return_value
        mock_instance.query_recent_data.return_value = []

        preprocessor = DataPreprocessor()
        df = preprocessor.fetch_raw_data(60)
        assert df.empty

def test_clean_and_smooth():
    # Create sample dataframe with some NaNs and noise
    df = pd.DataFrame({
        'ppm': [400.0, 410.0, np.nan, 450.0, 460.0],
        'voltage': [1.2, 1.25, 1.3, 1.35, 1.4]
    })

    with patch('src.pipeline.preprocessing.InfluxDBWrapper'):
        preprocessor = DataPreprocessor()
        cleaned_df = preprocessor.clean_and_smooth(df, window_size=2)

        # NaN should be dropped
        assert len(cleaned_df) == 4
        assert 'ppm_smoothed' in cleaned_df.columns
        # Smoothed values check
        # index 0: 400.0
        # index 1: (400.0+410.0)/2 = 405.0
        # index 3: (410.0+450.0)/2 = 430.0
        # index 4: (450.0+460.0)/2 = 455.0
        expected_smoothed = [400.0, 405.0, 430.0, 455.0]
        np.testing.assert_array_almost_equal(cleaned_df['ppm_smoothed'].values, expected_smoothed)

def test_create_lstm_sequences():
    with patch('src.pipeline.preprocessing.InfluxDBWrapper'):
        preprocessor = DataPreprocessor()

        df = pd.DataFrame({
            'ppm_smoothed': [1, 2, 3, 4, 5]
        })

        X, y = preprocessor.create_lstm_sequences(df, time_steps=3)

        # Expected X: [[[1], [2], [3]], [[2], [3], [4]]]
        # Expected y: [4, 5]
        assert X.shape == (2, 3, 1)
        assert y.shape == (2,)
        np.testing.assert_array_equal(y, [4, 5])
