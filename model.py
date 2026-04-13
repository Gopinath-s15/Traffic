import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
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
    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, predictions)
    print(f"Model trained successfully. Accuracy on test: {test_acc * 100:.2f}%")
    
    # Modern Dark Cyberpunk Graph
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('#0b1121')
    ax.set_facecolor('#0b1121')
    
    categories = ['Training Accuracy', 'Testing Accuracy']
    accuracies = [train_acc * 100, test_acc * 100]
    
    bars = ax.bar(categories, accuracies, color='#00f2fe', edgecolor='#4facfe', linewidth=2, width=0.4)
    for bar in bars:
        bar.set_alpha(0.8)
        
    ax.set_title("Random Forest Performance", color='#ffffff', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel("Accuracy (%)", color='#a0aec0', fontsize=12)
    ax.tick_params(colors='#a0aec0', labelsize=11)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Matplotlib uses tuples for RGBA: (r, g, b, alpha) with values 0 to 1
    spine_color = (0, 242/255, 254/255, 0.3)
    ax.spines['bottom'].set_color(spine_color)
    ax.spines['left'].set_color(spine_color)
    
    ax.set_ylim(0, 115)
    
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{yval:.1f}%", ha='center', va='bottom', color='#ffffff', fontweight='bold', fontsize=12)

    plt.tight_layout()
    plt.savefig("accuracy_graph.png", facecolor=fig.get_facecolor(), transparent=True)
    plt.close()

    joblib.dump(model, MODEL_FILE)
    print(f"Model saved to {MODEL_FILE}")

if __name__ == '__main__':
    train_model()
