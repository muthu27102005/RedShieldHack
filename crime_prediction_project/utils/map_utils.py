import folium
from folium.plugins import HeatMap

def get_base_map(df, zoom=7):
    """Returns a map centered around the dataset's mean coordinates."""
    if df is None or df.empty:
        return folium.Map(location=[11.1271, 78.6569], zoom_start=7, tiles="cartodbdark_matter")
    
    # Dynamic Tactical Zoom Engine: If data is filtered massively (like a city filter), automatically zoom into it natively!
    dynamic_zoom = 12 if len(df) < 1000 else 7
    map_center = [df['latitude'].mean(), df['longitude'].mean()]
    return folium.Map(location=map_center, zoom_start=dynamic_zoom, tiles="cartodbdark_matter")

def generate_heatmap(df):
    """Generates a folium map with a heatmap layer."""
    m = get_base_map(df)
    if df is not None and not df.empty:
        heat_data = [[row['latitude'], row['longitude']] for index, row in df.iterrows()]
        HeatMap(heat_data, radius=15, blur=20, max_zoom=1).add_to(m)
    return m._repr_html_()

def generate_prediction_map(df, hotspots, route):
    """Generates a prediction map with hotspots and patrol routes."""
    m = get_base_map(df)
    
    # Optimization: We intentionally bypass rendering thousands of raw data points
    # on the predictive layer to maintain high-performance Command Center UI rendering.

    # Plot Hotspots
    for i, center in enumerate(hotspots):
        folium.Marker(
            location=[center[0], center[1]],
            popup=f"<strong>Hotspot {i+1}</strong>",
            icon=folium.Icon(color='red', icon='fire', prefix='fa')
        ).add_to(m)
        
        folium.Circle(
            location=[center[0], center[1]],
            radius=500,
            color='red',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
        
    # Plot Patrol Route
    if len(route) > 1:
        folium.PolyLine(
            route,
            color='#4deeea',
            weight=4,
            opacity=0.8,
            dash_array='10, 10'
        ).add_to(m)

    return m._repr_html_()
