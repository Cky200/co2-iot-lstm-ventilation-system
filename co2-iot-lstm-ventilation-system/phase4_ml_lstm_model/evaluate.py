import os
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from . import config
from .data_processor import generate_synthetic_data, prepare_data, load_scaler

def evaluate():
    """
    Evaluates the saved model on a new set of synthetic data.
    """
    if not os.path.exists(config.MODEL_SAVE_PATH):
        raise FileNotFoundError(f"Model not found at {config.MODEL_SAVE_PATH}. Please run train.py first.")
        
    print("Loading model and scaler...")
    model = load_model(config.MODEL_SAVE_PATH)
    scaler = load_scaler(config.SCALER_SAVE_PATH)
    
    print("Generating test data...")
    # Generate new unseen data for evaluation
    df = generate_synthetic_data(num_samples=500)
    
    # We must use the same scaler fitted during training!
    scaled_data = scaler.transform(df[["co2"]].values)
    
    X_test, y_test = [], []
    for i in range(len(scaled_data) - config.SEQUENCE_LENGTH):
        X_test.append(scaled_data[i:(i + config.SEQUENCE_LENGTH), 0])
        y_test.append(scaled_data[i + config.SEQUENCE_LENGTH, 0])
        
    X_test, y_test = np.array(X_test), np.array(y_test)
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], config.FEATURES))
    
    print("Predicting...")
    predictions_scaled = model.predict(X_test)
    
    # Inverse transform to get actual CO2 values
    y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
    predictions_inv = scaler.inverse_transform(predictions_scaled)
    
    # Calculate metrics
    mse = mean_squared_error(y_test_inv, predictions_inv)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test_inv, predictions_inv)
    r2 = r2_score(y_test_inv, predictions_inv)
    
    print("-" * 30)
    print("Evaluation Metrics:")
    print(f"MSE:  {mse:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE:  {mae:.2f}")
    print(f"R2:   {r2:.2f}")
    print("-" * 30)
    
    return {"mse": mse, "rmse": rmse, "mae": mae, "r2": r2}

if __name__ == "__main__":
    evaluate()
