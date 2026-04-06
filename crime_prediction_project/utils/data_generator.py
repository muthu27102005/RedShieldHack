import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_realistic_data(filepath='data/crime_data_tn.csv', num_records=1500):
    """Generates a highly realistic, large-scale synthetic crime dataset centered around Tamil Nadu."""

    data = []
    crime_types = ['Theft', 'Assault', 'Burglary', 'Vandalism', 'Narcotics', 'Robbery']
    crime_probs = [0.35, 0.20, 0.15, 0.15, 0.10, 0.05]
    
    # Weather context suited for India
    weather_conditions = ['Clear', 'Rain', 'Fog', 'Extreme Heat']
    
    start_date = datetime(2023, 1, 1)

    for _ in range(num_records):
        # Create concentrated hotspots using normal distribution over Tamil Nadu
        rand_loc = random.random()
        if rand_loc > 0.6:
            # Hotspot 1 (Chennai - Shifted deeply Inland towards Anna Nagar/Porur)
            lat = np.random.normal(13.0500, 0.04)
            lon = np.random.normal(80.1900, 0.03)
            # Hard limit prevent any drift into the ocean (Longitude > 80.26 is the beach/water)
            lon = min(lon, 80.25)
        elif rand_loc > 0.25:
            # Hotspot 2 (Coimbatore - Safely Inland)
            lat = np.random.normal(11.0168, 0.03)
            lon = np.random.normal(76.9558, 0.03)
        elif rand_loc > 0.1:
            # Hotspot 3 (Madurai - Safely Inland)
            lat = np.random.normal(9.9252, 0.03)
            lon = np.random.normal(78.1198, 0.03)
        else:
            # Hotspot 4 (Tiruchirappalli - Safely Inland replacing the random water risk)
            lat = np.random.normal(10.7905, 0.05)
            lon = np.random.normal(78.7047, 0.05)

        ctype = np.random.choice(crime_types, p=crime_probs)
        
        # Correlate time and crime (e.g. Assaults at night)
        if ctype in ['Assault', 'Burglary', 'Robbery']:
            hour = np.random.choice(list(range(18, 24)) + list(range(0, 6)))
        else:
            hour = random.randint(0, 23)
            
        minute = random.randint(0, 59)
        time_str = f"{hour:02d}:{minute:02d}"
        
        # Calculate random date
        random_days = random.randint(0, 365)
        d = start_date + timedelta(days=random_days)
        date_str = d.strftime("%Y-%m-%d")
        
        weather = np.random.choice(weather_conditions, p=[0.5, 0.25, 0.15, 0.10])
        
        # Severity calculation (1-10)
        severity = random.randint(1, 4)
        if ctype in ['Assault', 'Robbery']: severity += random.randint(3, 6)
        if weather in ['Rain', 'Extreme Heat']: severity += 1
        severity = min(severity, 10)
        
        data.append({
            'incident_id': f"TN-FIR-{random.randint(100000, 999999)}",
            'latitude': round(lat, 6),
            'longitude': round(lon, 6),
            'crime_type': ctype,
            'date': date_str,
            'time': time_str,
            'weather_condition': weather,
            'severity_index': severity
        })

    df = pd.DataFrame(data)
    
    import os
    if not os.path.exists('data'):
        os.makedirs('data')
        
    df.to_csv(filepath, index=False)
    print(f"Generated {num_records} realistic India-specific records at {filepath}")

if __name__ == '__main__':
    generate_realistic_data()
