import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

DATA_FILE = 'traffic_data.csv'
MODEL_FILE = 'model.pkl'

def generate_synthetic_data(num_samples=500):
    np.random.seed(42)
    # Speed: 20 to 120 km/h
    speeds = np.random.randint(20, 121, num_samples)
    
    # Weather: 0 (Clear), 1 (Rainy), 2 (Foggy/Snow)
    weathers = np.random.randint(0, 3, num_samples)
    
    # Time: 0 (Day), 1 (Night)
    times = np.random.randint(0, 2, num_samples)
    
    # Risk Logic
    # High risk (2) if (Speed > 80 and Weather > 0) or (Speed > 100) or (Speed > 70 and Weather == 2 and Time == 1)
    # Medium risk (1) if (Speed > 60 and Weather > 0) or (Speed > 80)
    # Low risk (0) otherwise
    
    risks = []
    for s, w, t in zip(speeds, weathers, times):
        # Change: s >= 80 instead of s > 80 to match exact requirements (Speed = 80, Rainy = High Risk)
        if (s >= 80 and w > 0) or (s >= 100) or (s > 70 and w == 2 and t == 1):
            risks.append(2) # High Risk
        elif (s > 60 and w > 0) or (s > 70):
            risks.append(1) # Medium Risk
        else:
            risks.append(0) # Low Risk
            
    df = pd.DataFrame({
        'speed': speeds,
        'weather': weathers,
        'time': times,
        'risk': risks
    })
    
    df.to_csv(DATA_FILE, index=False)
    print(f"Synthetic dataset with {num_samples} samples generated and saved to {DATA_FILE}.")
    return df

def train_model():
    if not os.path.exists(DATA_FILE):
        df = generate_synthetic_data(1000)
    else:
        df = pd.read_csv(DATA_FILE)
        print(f"Loaded existing dataset from {DATA_FILE}.")

    X = df[['speed', 'weather', 'time']]
    y = df['risk']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"Model trained successfully. Accuracy on test set: {acc * 100:.2f}%")
    
    joblib.dump(model, MODEL_FILE)
    print(f"Model saved to {MODEL_FILE}")

if __name__ == '__main__':
    train_model()
