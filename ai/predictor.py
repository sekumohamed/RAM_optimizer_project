import sqlite3
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
from utils.logger import get_logger
from utils.config import DB_PATH, PREDICTION_HORIZON_MINUTES

logger = get_logger(__name__)

# Path to save trained model
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'ram_predictor.pkl')

def load_training_data() -> pd.DataFrame:
    # Load RAM snapshots from database into a DataFrame
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT timestamp, used_mb, percent_used, swap_percent
        FROM ram_snapshots
        ORDER BY timestamp ASC
    ''', conn)
    conn.close()

    if df.empty:
        logger.warning("No training data available yet.")
        return df

    # Parse timestamp and extract time features
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['day_of_month'] = df['timestamp'].dt.day

    return df

def prepare_features(df: pd.DataFrame) -> tuple:
    # Prepare features and target for training
    feature_cols = ['hour', 'minute', 'day_of_week', 'day_of_month', 'swap_percent']
    target_col = 'percent_used'

    df = df.dropna(subset=feature_cols + [target_col])

    X = df[feature_cols].values
    y = df[target_col].values

    return X, y

def train_model() -> dict:
    # Train RAM usage prediction model
    logger.info("Loading training data...")
    df = load_training_data()

    if df.empty or len(df) < 10:
        logger.warning("Not enough data to train model. Need at least 10 samples.")
        return {'status': 'insufficient_data', 'samples': len(df)}

    X, y = prepare_features(df)

    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Try Random Forest first, fall back to Linear Regression
    if len(X_train) >= 20:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model_name = 'RandomForest'
    else:
        model = LinearRegression()
        model_name = 'LinearRegression'

    model.fit(X_train, y_train)

    # Evaluate model
    y_pred = model.predict(X_test)
    mae = round(mean_absolute_error(y_test, y_pred), 2)

    # Save model to disk
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Model trained ({model_name}) — MAE: {mae}% | Samples: {len(X)}")

    return {
        'status': 'success',
        'model': model_name,
        'mae': mae,
        'samples': len(X)
    }

def load_model():
    # Load trained model from disk
    if not os.path.exists(MODEL_PATH):
        logger.warning("No trained model found. Training now...")
        result = train_model()
        if result['status'] != 'success':
            return None

    return joblib.load(MODEL_PATH)

def predict_ram_usage(minutes_ahead: int = None) -> dict:
    # Predict RAM usage at a future time
    if minutes_ahead is None:
        minutes_ahead = PREDICTION_HORIZON_MINUTES

    model = load_model()
    if model is None:
        return {'status': 'model_unavailable'}

    # Build feature vector for future time
    future_time = datetime.now() + timedelta(minutes=minutes_ahead)
    features = np.array([[
        future_time.hour,
        future_time.minute,
        future_time.weekday(),
        future_time.day,
        0.0   # assume swap at 0 for prediction
    ]])

    predicted_percent = round(float(model.predict(features)[0]), 2)
    predicted_percent = max(0.0, min(100.0, predicted_percent))

    # Determine risk level
    if predicted_percent >= 90:
        risk = 'CRITICAL'
    elif predicted_percent >= 80:
        risk = 'WARNING'
    elif predicted_percent >= 60:
        risk = 'MODERATE'
    else:
        risk = 'HEALTHY'

    result = {
        'status': 'success',
        'predicted_at': future_time.strftime('%Y-%m-%d %H:%M:%S'),
        'predicted_percent': predicted_percent,
        'risk_level': risk,
        'minutes_ahead': minutes_ahead
    }

    logger.info(
        f"Prediction ({minutes_ahead} min ahead): "
        f"{predicted_percent}% RAM usage | Risk: {risk}"
    )

    return result

def run_prediction_cycle() -> list:
    # Predict RAM usage for multiple horizons
    horizons = [15, 30, 60]
    results = []

    logger.info("Running prediction cycle...")

    # Retrain model with latest data
    train_model()

    for horizon in horizons:
        result = predict_ram_usage(minutes_ahead=horizon)
        results.append(result)

    return results