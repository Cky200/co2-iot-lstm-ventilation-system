import pytest
from phase4_ml_lstm_model.model import build_lstm_model

def test_build_lstm_model():
    input_shape = (10, 1)
    model = build_lstm_model(input_shape=input_shape)
    
    # Check if compiled
    assert model.optimizer is not None
    assert model.loss == 'mean_squared_error'
    
    # Check input shape
    assert model.input_shape == (None, 10, 1)
    
    # Check output shape
    assert model.output_shape == (None, 1)
    
    # Check layer types roughly
    layers = [type(layer).__name__ for layer in model.layers]
    assert 'LSTM' in layers
    assert 'Dense' in layers
