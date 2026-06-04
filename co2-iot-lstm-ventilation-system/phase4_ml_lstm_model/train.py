import os
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, TensorBoard
from sklearn.model_selection import train_test_split

from . import config
from .data_processor import generate_synthetic_data, prepare_data, save_scaler
from .model import build_lstm_model

def train():
    """
    Trains the LSTM model using synthetic data and saves the best model and scaler.
    """
    print("Generating synthetic data...")
    df = generate_synthetic_data(num_samples=2000)
    
    print("Preparing data...")
    X, y, scaler = prepare_data(df, sequence_length=config.SEQUENCE_LENGTH)
    
    # Train-test split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"X_val shape: {X_val.shape}, y_val shape: {y_val.shape}")
    
    print("Building model...")
    model = build_lstm_model(input_shape=(config.SEQUENCE_LENGTH, config.FEATURES))
    model.summary()
    
    # Callbacks
    early_stopping = EarlyStopping(
        monitor='val_loss', 
        patience=5, 
        restore_best_weights=True
    )
    
    model_checkpoint = ModelCheckpoint(
        filepath=config.MODEL_SAVE_PATH,
        monitor='val_loss',
        save_best_only=True,
        verbose=1
    )
    
    tensorboard_logs = os.path.join(config.BASE_DIR, "logs")
    tensorboard = TensorBoard(log_dir=tensorboard_logs)
    
    callbacks = [early_stopping, model_checkpoint, tensorboard]
    
    print("Starting training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=config.EPOCHS,
        batch_size=config.BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )
    
    print(f"Training completed. Model saved at {config.MODEL_SAVE_PATH}")
    
    # Save the scaler for later inference
    save_scaler(scaler, config.SCALER_SAVE_PATH)
    print(f"Scaler saved at {config.SCALER_SAVE_PATH}")
    
    return history, model

if __name__ == "__main__":
    train()
