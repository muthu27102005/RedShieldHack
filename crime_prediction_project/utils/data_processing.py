import pandas as pd
import os

def load_data(filepath):
    """Loads CSV data using pandas."""
    if not os.path.exists(filepath):
        return None
    return pd.read_csv(filepath)

def get_crime_types(df):
    """Returns a list of unique crime types from the dataframe."""
    if df is None or 'crime_type' not in df.columns:
        return []
    return df['crime_type'].dropna().unique().tolist()

def filter_by_crime_type(df, crime_type):
    """Filters the dataframe by a specific crime type."""
    if df is None or crime_type == "All" or not crime_type:
        return df
    return df[df['crime_type'] == crime_type]
