import os
import pandas as pd
import folium
from folium.plugins import HeatMap
from sklearn.cluster import KMeans
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATA_FILE = os.path.join(UPLOAD_FOLDER, 'uploaded_data.csv')

def get_base_map(df, zoom=12):
    """Helper function to get a map centered on data average coordinates."""
    if df.empty:
        return folium.Map(location=[0, 0], zoom_start=2, tiles="cartodbdark_matter")
    # Center map on the mean coordinates
    map_center = [df['latitude'].mean(), df['longitude'].mean()]
    return folium.Map(location=map_center, zoom_start=zoom, tiles="cartodbdark_matter")


@app.route('/')
def index():
    """Homepage: Dashboard and Data Upload"""
    data_exists = os.path.exists(DATA_FILE)
    return render_template('index.html', data_exists=data_exists)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle CSV data upload"""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_data.csv')
        file.save(filepath)
        flash('Data successfully uploaded and processed!')
        return redirect(url_for('map_view'))
    else:
        flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
        return redirect(url_for('index'))

@app.route('/map', methods=['GET', 'POST'])
def map_view():
    """Display Heatmap and optionally filter by Crime Type"""
    if not os.path.exists(DATA_FILE):
        flash("Please upload data first!")
        return redirect(url_for('index'))
    
    df = pd.read_csv(DATA_FILE)
    
    # Get distinct crime types for filter dropdown
    crime_types = df['crime_type'].unique().tolist()
    
    # Apply filter if method is POST
    selected_type = request.form.get('crime_type') if request.method == 'POST' else None
    
    if selected_type and selected_type != "All":
        df = df[df['crime_type'] == selected_type]
    
    # Generate Map
    m = get_base_map(df)
    
    # Create HeatMap data format (list of lists: [lat, lon])
    heat_data = [[row['latitude'], row['longitude']] for index, row in df.iterrows()]
    
    # Add HeatMap to map
    HeatMap(heat_data, radius=15, blur=20, max_zoom=1).add_to(m)
    
    # Get HTML string for the Map
    map_html = m._repr_html_()
    
    return render_template('map.html', map_html=map_html, crime_types=crime_types, selected_type=selected_type)

@app.route('/predict')
def predict_view():
    """Apply KMeans Clustering and generate Patrol Route"""
    if not os.path.exists(DATA_FILE):
        flash("Please upload data first!")
        return redirect(url_for('index'))
    
    df = pd.read_csv(DATA_FILE)
    
    # We need coordinates for KMeans
    coords = df[['latitude', 'longitude']].values
    
    # Apply KMeans (Find 3 hotspots as default)
    # n_clusters could ideally be dynamic
    num_clusters = min(3, len(df))
    kmeans = KMeans(n_clusters=num_clusters, n_init=10, random_state=42)
    df['cluster'] = kmeans.fit_predict(coords)
    hotspots = kmeans.cluster_centers_
    
    m = get_base_map(df)
    
    # Add original data points as subtle dots
    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3,
            color='rgba(255,255,255,0.2)',
            fill=True
        ).add_to(m)
    
    patrol_route = []
    
    # Mark the hotspots with special UI markers
    for i, center in enumerate(hotspots):
        patrol_route.append([center[0], center[1]])
        folium.Marker(
            location=[center[0], center[1]],
            popup=f"<strong>High Risk Hotspot {i+1}</strong>",
            icon=folium.Icon(color='red', icon='fire', prefix='fa')
        ).add_to(m)
        
        # Draw a pulse circle around hotspot
        folium.Circle(
            location=[center[0], center[1]],
            radius=500, # meters
            color='red',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
    
    # Connect Hotspots to simulate simple Patrol Route
    if len(patrol_route) > 1:
        # Drawing route connecting hotspots back to the start (closed loop)
        patrol_route.append(patrol_route[0]) 
        folium.PolyLine(
            patrol_route,
            color='#4deeea',
            weight=4,
            opacity=0.8,
            dash_array='10, 10'
        ).add_to(m)
        
    map_html = m._repr_html_()
    
    return render_template('predict.html', map_html=map_html, num_clusters=num_clusters)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
