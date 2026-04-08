
# lstm_model.py
import torch  # type: ignore
import torch.nn as nn  # type: ignore
import torch.optim as optim  # type: ignore
import numpy as np  # type: ignore
import os

FEATURE_COLS  = ["returns", "ma10", "ma50", "rsi", "volatility", "macd", "signal", "bb_position"]
FEATURE_COUNT = len(FEATURE_COLS)  # 8
SEQ_LEN       = 30


# ---------------------------------------
# MODEL
# ---------------------------------------
class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm    = nn.LSTM(FEATURE_COUNT, 64, 2, batch_first=True, dropout=0.2)
        self.dropout = nn.Dropout(0.2)
        self.fc      = nn.Linear(64, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out    = self.dropout(out[:, -1, :])
        return self.fc(out)


# ---------------------------------------
# TRAINING
# ---------------------------------------
def train_lstm(df, epochs=50, batch_size=32):

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        print(f"Missing features for LSTM training: {missing}")
        return None

    data = df[FEATURE_COLS].values.astype(np.float32)

    if not np.isfinite(data).all():
        print("Non-finite values in training data — cleaning...")
        data = np.nan_to_num(data, nan=0.0, posinf=1.0, neginf=-1.0)

    if len(data) < SEQ_LEN + 1:
        print(f"Not enough data for LSTM training: {len(data)} rows")
        return None

    model = LSTMModel()

    X, y = [], []
    for i in range(len(data) - SEQ_LEN):
        X.append(data[i : i + SEQ_LEN])
        y.append(data[i + SEQ_LEN][0])  # predicting next return

    if len(X) == 0:
        print("No sequences created")
        return None

    X = torch.tensor(np.array(X), dtype=torch.float32)
    y = torch.tensor(np.array(y), dtype=torch.float32)

    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)  
    loss_fn   = nn.MSELoss()
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)  

    model.train()

    dataset = torch.utils.data.TensorDataset(X, y)
    loader  = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    for epoch in range(epochs):
        epoch_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            out  = model(xb).squeeze()
            loss = loss_fn(out, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item()
        scheduler.step()
        if epoch % 10 == 0:
            print(f"  Epoch {epoch}/{epochs} — loss: {epoch_loss / len(loader):.6f}")

    model.eval()
    print("LSTM training complete")
    return model


# ---------------------------------------
# PREDICTION
# ---------------------------------------
def predict_lstm(model, df):

    try:
        missing = [c for c in FEATURE_COLS if c not in df.columns]
        if missing:
            print(f" Missing features for prediction: {missing}")
            return None

        if len(df) < SEQ_LEN:
            print(f"Not enough rows for prediction: need {SEQ_LEN}, got {len(df)}")
            return None

        seq  = df.tail(SEQ_LEN)[FEATURE_COLS].values.astype(np.float32)

        if not np.isfinite(seq).all():
            seq = np.nan_to_num(seq, nan=0.0, posinf=1.0, neginf=-1.0)

        seq_tensor = torch.tensor(seq, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            pred = model(seq_tensor).item()

        if not np.isfinite(pred):
            print("LSTM returned non-finite prediction")
            return None

        # Convert predicted return → price
        last_price      = float(df["Close"].iloc[-1])
        predicted_price = last_price * (1 + pred)

        if abs(predicted_price - last_price) / (last_price + 1e-6) > 0.5:
            print(f" Prediction {predicted_price:.2f} too far from current {last_price:.2f} — clamping")
            predicted_price = last_price * (1 + np.clip(pred, -0.5, 0.5))

        return float(predicted_price)

    except Exception as e:
        print(f"LSTM prediction error: {e}")
        return None


# ---------------------------------------
# MODEL STORAGE
# ---------------------------------------
BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models_store", "lstm.pth")


def save_lstm(model):
    try:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)  
        torch.save(model.state_dict(), MODEL_PATH)
        print("LSTM model saved")
    except Exception as e:
        print(f"Save error: {e}")


def load_lstm():
    try:
        if not os.path.exists(MODEL_PATH):
            print(" No saved LSTM model — will train fresh")
            return None

        model = LSTMModel()
        model.load_state_dict(
            torch.load(MODEL_PATH, map_location=torch.device("cpu"), weights_only=True)
        )
        model.eval()
        print("LSTM model loaded")
        return model

    except Exception as e:
        print(f"Load error: {e} — will retrain")
        return None     