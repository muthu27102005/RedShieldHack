import os
import joblib
from sklearn.cluster import KMeans

MODELS_DIR = 'models'
MODEL_PATH = os.path.join(MODELS_DIR, 'kmeans_model.pkl')

def train_kmeans(df, num_clusters=3):
    """Trains a KMeans model and returns the hotspots and patrol route."""
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

    coords = df[['latitude', 'longitude']].values
    num_clusters = min(num_clusters, len(df))
    
    kmeans = KMeans(n_clusters=num_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(coords)
    
    hotspots = kmeans.cluster_centers_
    
    # Save the model
    joblib.dump(kmeans, MODEL_PATH)

    # Build patrol route (closed loop)
    patrol_route = []
    for center in hotspots:
        patrol_route.append([center[0], center[1]])
    
    if len(patrol_route) > 1:
        patrol_route.append(patrol_route[0])
        
    return hotspots, patrol_route, num_clusters
