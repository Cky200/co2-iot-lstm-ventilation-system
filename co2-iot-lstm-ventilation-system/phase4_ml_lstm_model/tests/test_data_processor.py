import pytest
import numpy as np
from phase4_ml_lstm_model.data_processor import generate_synthetic_data, prepare_data
from phase4_ml_lstm_model import config

def test_generate_synthetic_data():
    df = generate_synthetic_data(num_samples=100)
    assert len(df) == 100
    assert "co2" in df.columns
    assert not df["co2"].isnull().any()

def test_prepare_data():
    df = generate_synthetic_data(num_samples=50)
    X, y, scaler = prepare_data(df, sequence_length=10)
    
    # Check shapes
    expected_samples = 50 - 10
    assert X.shape == (expected_samples, 10, 1)
    assert y.shape == (expected_samples,)
    
    # Check scaling (should be within 0 and 1)
    assert np.all(X >= 0) and np.all(X <= 1)
    assert np.all(y >= 0) and np.all(y <= 1)
