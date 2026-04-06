import os
os.environ["OMP_NUM_THREADS"] = "1"  # Fix for Scikit-Learn KMeans freezing inside Windows Flask threads
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
from utils.data_processing import load_data, get_crime_types, filter_by_crime_type
from utils.map_utils import generate_heatmap, generate_prediction_map
from utils.model import train_kmeans

app = Flask(__name__)
app.secret_key = 'omni-cortex-secure-x99'

DATA_DIR = 'data'
DATA_FILE = os.path.join(DATA_DIR, 'crime_data_tn.csv')

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
            file.save(DATA_FILE)
            flash('Database successfully integrated and encrypted.')
            return redirect(url_for('dashboard'))
        else:
            flash('Corrupted or invalid datastream. CSV required.')
    return render_template('upload.html')

@app.route('/log_fir', methods=['GET', 'POST'])
def log_fir():
    if request.method == 'POST':
        # Grab form data
        address = request.form.get('address')
        ctype = request.form.get('crime_type')
        weather = request.form.get('weather_condition')
        severity = request.form.get('severity_index')
        
        # Geocode the address
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="predict_guard_app")
        location = geolocator.geocode(address)
        
        if not location:
            flash(f"Could not pinpoint coordinates for address '{address}'. Please provide a more specific location.")
            return redirect(url_for('log_fir'))
            
        lat = location.latitude
        lon = location.longitude
        
        # Auto-generate current date and time
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M')
        incident_id = f"NYPD-ACT-{now.strftime('%H%M%S')}"
        
        new_record = pd.DataFrame([{
            'incident_id': incident_id,
            'latitude': float(lat),
            'longitude': float(lon),
            'crime_type': ctype,
            'date': date_str,
            'time': time_str,
            'weather_condition': weather,
            'severity_index': int(severity)
        }])
        
        # Append to CSV
        try:
            if os.path.exists(DATA_FILE):
                df = pd.read_csv(DATA_FILE)
                df = pd.concat([df, new_record], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
            else:
                if not os.path.exists(DATA_DIR):
                    os.makedirs(DATA_DIR)
                new_record.to_csv(DATA_FILE, index=False)
                
            flash(f"FIR {incident_id} officially logged at coordinates ({lat:.4f}, {lon:.4f}) and injected into the Neural Threat Matrix.")
        except PermissionError:
            flash("ACCESS DENIED: The database file (crime_data.csv) is locked. Please close Microsoft Excel or any open editors holding the file to allow the system to write to it.", "error")
        return redirect(url_for('dashboard'))
        
    return render_template('fir.html')

@app.route('/dashboard')
def dashboard():
    df = load_data(DATA_FILE)
    if df is None or df.empty:
        return redirect(url_for('upload'))
    
    # Calculate some real-world metrics for the command center
    total_incidents = len(df)
    high_severity = len(df[df['severity_index'] >= 7]) if 'severity_index' in df.columns else 0
    top_crime = df['crime_type'].mode()[0] if not df.empty else "N/A"
    
    # Grab the 5 most recent incidents
    recent_incidents = df.tail(5).to_dict('records')[::-1]
    
    return render_template('dashboard.html', 
                           total=total_incidents, 
                           severe=high_severity, 
                           top_crime=top_crime,
                           recent_incidents=recent_incidents)

@app.route('/api/crime_trends')
def crime_trends():
    df = load_data(DATA_FILE)
    if df is None:
        return jsonify({})
    
    # Initialize all 24 hours to 0 to prevent broken/collapsed graph axes
    hourly_counts = {int(i): 0 for i in range(24)}
    
    if 'time' in df.columns:
        df['hour'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.hour
        counts = df['hour'].value_counts().to_dict()
        for hour_val, count in counts.items():
            if pd.notna(hour_val):
                hourly_counts[int(hour_val)] = int(count)
                
    return jsonify(hourly_counts)

@app.route('/map', methods=['GET', 'POST'])
def view_map():
    df = load_data(DATA_FILE)
    if df is None: return redirect(url_for('upload'))
    
    crime_types = get_crime_types(df)
    selected_type = request.form.get('crime_type') if request.method == 'POST' else None
    
    df_filtered = filter_by_crime_type(df, selected_type)
    map_html = generate_heatmap(df_filtered)
    
    return render_template('map.html', map_html=map_html, crime_types=crime_types, selected_type=selected_type)

@app.route('/predict', methods=['GET', 'POST'])
def result():
    df = load_data(DATA_FILE)
    if df is None: return redirect(url_for('upload'))
    
    weather_focus = "All"
    target_shift = "All"
    units = 3

    if request.method == 'POST':
        weather_focus = request.form.get('weather')
        target_shift = request.form.get('shift')
        units = int(request.form.get('units', 3))
        
        if weather_focus and weather_focus != "All" and 'weather_condition' in df.columns:
            df = df[df['weather_condition'] == weather_focus]
        
        if target_shift and target_shift != "All" and 'time' in df.columns:
            df['hour'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.hour
            if target_shift == "Night":
                df = df[(df['hour'] >= 18) | (df['hour'] < 6)]
            elif target_shift == "Day":
                df = df[(df['hour'] >= 6) & (df['hour'] < 18)]

    # Dynamic K based on units available
    num_clusters = min(units, len(df))
    if num_clusters == 0:
        flash('No data matches the selected operational constraints.')
        return redirect(url_for('dashboard'))

    hotspots, patrol_route, num_clusters = train_kmeans(df, num_clusters=num_clusters)
    map_html = generate_prediction_map(df, hotspots, patrol_route)
    
    return render_template('result.html', map_html=map_html, num_clusters=num_clusters, units=units)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
