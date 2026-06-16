import os
import pickle

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from . import config


def generate_synthetic_data(num_samples=1000):
    """
    Generates synthetic CO2 time-series data for testing and development.
    Simulates a baseline of 400ppm with some daily cycles and noise.
    """
    time = np.arange(0, num_samples)
    # Baseline 400, sine wave to simulate daily cycle, plus some random noise
    co2_levels = 400 + 100 * np.sin(2 * np.pi * time / 100) + np.random.normal(0, 10, num_samples)

    df = pd.DataFrame({"co2": co2_levels})
    return df

def prepare_data(df, sequence_length=config.SEQUENCE_LENGTH):
    """
    Scales data and creates sequences for LSTM.
    Returns X, y, and the fitted scaler.
    """
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df[["co2"]].values)

    X, y = [], []
    for i in range(len(scaled_data) - sequence_length):
        X.append(scaled_data[i:(i + sequence_length), 0])
        y.append(scaled_data[i + sequence_length, 0])

    X, y = np.array(X), np.array(y)

    # Reshape X to be [samples, time steps, features]
    X = np.reshape(X, (X.shape[0], X.shape[1], config.FEATURES))

    return X, y, scaler

def save_scaler(scaler, filepath=config.SCALER_SAVE_PATH):
    """Saves the fitted scaler for inference."""
    with open(filepath, 'wb') as f:
        pickle.dump(scaler, f)

def load_scaler(filepath=config.SCALER_SAVE_PATH):
    """Loads the fitted scaler."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Scaler not found at {filepath}")
    with open(filepath, 'rb') as f:
        scaler = pickle.load(f)
    return scaler
