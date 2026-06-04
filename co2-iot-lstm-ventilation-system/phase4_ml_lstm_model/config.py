import os

# Model hyperparameters
SEQUENCE_LENGTH = 10
FEATURES = 1  # Using only CO2 for now
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.001

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "saved_model", "lstm_co2_model.keras")
SCALER_SAVE_PATH = os.path.join(BASE_DIR, "saved_model", "scaler.pkl")

# Ensure save directory exists
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
