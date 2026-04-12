from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import joblib
import pandas as pd
import os

app = Flask(__name__)

# Constants
DATABASE = 'database.db'
MODEL_FILE = 'model.pkl'

# Initialize SQLite Database+
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                speed INTEGER,
                weather INTEGER,
                time INTEGER,
                risk_level TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# Load Model
try:
    model = joblib.load(MODEL_FILE)
except FileNotFoundError:
    model = None
    print(f"Warning: {MODEL_FILE} not found. Ensure model is trained.")

# Define Risk Levels mapping
RISK_MAPPING = {
    0: 'LOW RISK',
    1: 'MEDIUM RISK',
    2: 'HIGH RISK'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded.'}), 500
        
    data = request.json
    try:
        speed = int(data['speed'])
        weather = int(data['weather'])
        time = int(data['time'])
    except (KeyError, ValueError):
        return jsonify({'error': 'Invalid input data.'}), 400

    # Format input for model
    features = pd.DataFrame([[speed, weather, time]], columns=['speed', 'weather', 'time'])
    
    # Predict
    prediction = model.predict(features)[0]
    risk_level = RISK_MAPPING.get(prediction, 'UNKNOWN')
    
    # Save to Database
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (speed, weather, time, risk_level) 
            VALUES (?, ?, ?, ?)
        ''', (speed, weather, time, risk_level))
        conn.commit()

    return jsonify({
        'speed': speed,
        'weather': weather,
        'time': time,
        'risk': risk_level
    })

@app.route('/history', methods=['GET'])
def get_history():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT speed, weather, time, risk_level, timestamp FROM predictions ORDER BY id DESC LIMIT 50')
        rows = cursor.fetchall()
        
    history = []
    for row in rows:
        history.append({
            'speed': row[0],
            'weather': row[1],
            'time': row[2],
            'risk_level': row[3],
            'timestamp': row[4]
        })
        
    return jsonify(history)

@app.route('/history-view')
def history_page():
    return render_template('history.html')

@app.route('/graph-view')
def graph_page():
    return render_template('graph.html')

@app.route('/artifact-logo')
def artifact_logo():
    return send_from_directory(r'C:\Users\virat\.gemini\antigravity\brain\a4430a3a-2ef7-465c-9179-d74ef198c80f', 'traffic_logo_1776013508972.png')

@app.route('/accuracy-graph')
def accuracy_graph():
    return send_from_directory(r'c:\Users\virat\Desktop\traffic', 'accuracy_graph.png')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
