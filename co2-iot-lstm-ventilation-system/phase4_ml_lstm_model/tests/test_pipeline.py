import os
import shutil

import pytest
from phase4_ml_lstm_model.evaluate import evaluate
from phase4_ml_lstm_model.predict import predict_next_co2
from phase4_ml_lstm_model.train import train

from phase4_ml_lstm_model import config


@pytest.fixture(autouse=True)
def override_config_for_testing():
    # Override paths to avoid cluttering actual models
    original_model_path = config.MODEL_SAVE_PATH
    original_scaler_path = config.SCALER_SAVE_PATH
    original_epochs = config.EPOCHS
    original_batch = config.BATCH_SIZE

    # Use a temp directory
    test_dir = os.path.join(config.BASE_DIR, "tests", "temp_save")
    os.makedirs(test_dir, exist_ok=True)

    config.MODEL_SAVE_PATH = os.path.join(test_dir, "test_model.keras")
    config.SCALER_SAVE_PATH = os.path.join(test_dir, "test_scaler.pkl")
    config.EPOCHS = 1  # Fast training for test
    config.BATCH_SIZE = 16

    yield

    # Cleanup
    config.MODEL_SAVE_PATH = original_model_path
    config.SCALER_SAVE_PATH = original_scaler_path
    config.EPOCHS = original_epochs
    config.BATCH_SIZE = original_batch
    shutil.rmtree(test_dir, ignore_errors=True)

def test_full_pipeline():
    # 1. Train model
    history, model = train()
    assert os.path.exists(config.MODEL_SAVE_PATH)
    assert os.path.exists(config.SCALER_SAVE_PATH)

    # 2. Evaluate model
    metrics = evaluate()
    assert "mse" in metrics
    assert "rmse" in metrics

    # 3. Predict
    dummy_input = [400.0 + i for i in range(config.SEQUENCE_LENGTH)]
    pred = predict_next_co2(dummy_input)
    assert isinstance(pred, float)
