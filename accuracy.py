from sklearn.metrics import accuracy_score
import pandas as pd
import joblib

# Load dataset
data = pd.read_csv("traffic_data.csv")

X = data[['speed','weather','time']]
y = data['risk']

# Load model
model = joblib.load("model.pkl")

# Predict and calculate accuracy
y_pred = model.predict(X)
print("Accuracy:", accuracy_score(y, y_pred))
