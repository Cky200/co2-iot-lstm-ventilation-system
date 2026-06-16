import os

import numpy as np
from tensorflow.keras.models import load_model

from . import config
from .data_processor import load_scaler

# Cache model and scaler so they are not loaded on every prediction
_MODEL = None
_SCALER = None

def load_resources():
    global _MODEL, _SCALER
    if _MODEL is None:
        if not os.path.exists(config.MODEL_SAVE_PATH):
            raise FileNotFoundError(f"Model not found at {config.MODEL_SAVE_PATH}")
        _MODEL = load_model(config.MODEL_SAVE_PATH)

    if _SCALER is None:
        _SCALER = load_scaler(config.SCALER_SAVE_PATH)

def predict_next_co2(recent_readings):
    """
    Predicts the next CO2 level given the most recent readings.

    Args:
        recent_readings (list or np.array): A list of recent CO2 readings.
                                            Must be of length config.SEQUENCE_LENGTH.

    Returns:
        float: Predicted next CO2 level.
    """
    if len(recent_readings) != config.SEQUENCE_LENGTH:
        raise ValueError(f"Expected {config.SEQUENCE_LENGTH} readings, got {len(recent_readings)}")

    load_resources()

    # Convert to numpy array and reshape for scaler
    data = np.array(recent_readings).reshape(-1, 1)

    # Scale data
    scaled_data = _SCALER.transform(data)

    # Reshape for LSTM: [samples, time steps, features]
    # Here samples=1, time steps=SEQUENCE_LENGTH, features=FEATURES
    X = np.reshape(scaled_data, (1, config.SEQUENCE_LENGTH, config.FEATURES))

    # Predict
    predicted_scaled = _MODEL.predict(X, verbose=0)

    # Inverse scale
    predicted_inv = _SCALER.inverse_transform(predicted_scaled)

    return float(predicted_inv[0][0])
