import os
import sys
import tempfile
import shutil

# Get the root directory of the project (one level up from api/)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, 'static')

# Ensure Python can find modules in the root directory if needed
sys.path.append(base_dir)

from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import joblib
import pandas as pd

# Set explicit paths for templates and static folders relative to the root directory
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# --- Constants & Paths ---
# Vercel's filesystem is read-only. We must write to /tmp for SQLite to work.
original_db = os.path.join(base_dir, 'database.db')
vercel_tmp_db = os.path.join(tempfile.gettempdir(), 'database.db')

# Copy the DB to /tmp if it doesn't exist there so we can insert new predictions without a 500 error
if not os.path.exists(vercel_tmp_db) and os.path.exists(original_db):
    try:
        shutil.copy2(original_db, vercel_tmp_db)
    except Exception:
        pass

DATABASE = vercel_tmp_db if 'VERCEL' in os.environ or os.path.exists('/tmp') else original_db
MODEL_FILE = os.path.join(base_dir, 'model.pkl')

# --- Initialize SQLite Database ---
def init_db():
    try:
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
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

# --- Load Model ---
try:
    model = joblib.load(MODEL_FILE)
except FileNotFoundError:
    model = None
    print(f"Warning: {MODEL_FILE} not found. Ensure model is trained.")
except Exception as e:
    model = None
    print(f"Error loading model: {e}")

# Define Risk Levels mapping
RISK_MAPPING = {
    0: 'LOW RISK',
    1: 'MEDIUM RISK',
    2: 'HIGH RISK'
}

# --- Routes ---
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
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions (speed, weather, time, risk_level) 
                VALUES (?, ?, ?, ?)
            ''', (speed, weather, time, risk_level))
            conn.commit()
    except Exception as e:
        print(f"Database insertion failed: {e}")

    return jsonify({
        'speed': speed,
        'weather': weather,
        'time': time,
        'risk': risk_level
    })

@app.route('/history', methods=['GET'])
def get_history():
    try:
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
    except Exception as e:
        print(f"Database read failed: {e}")
        return jsonify([])

@app.route('/history-view')
def history_page():
    return render_template('history.html')

@app.route('/graph-view')
def graph_page():
    return render_template('graph.html')

@app.route('/artifact-logo')
def artifact_logo():
    # Attempting to load logo from brain path probably won't work perfectly on Vercel unless it's packaged.
    # Fallback to shield.png if missing.
    try:
        return send_from_directory(r'C:\Users\virat\.gemini\antigravity\brain\a4430a3a-2ef7-465c-9179-d74ef198c80f', 'traffic_logo_1776013508972.png')
    except Exception:
        return send_from_directory(os.path.join(base_dir, 'static'), 'shield.png')

@app.route('/accuracy-graph')
def accuracy_graph():
    return send_from_directory(base_dir, 'accuracy_graph.png')

# Handle PWA files at root scope for proper installation
@app.route('/sw.js')
def serve_sw():
    return send_from_directory(static_dir, 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(static_dir, 'manifest.json', mimetype='application/manifest+json')

# Special handler for Vercel routing static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
