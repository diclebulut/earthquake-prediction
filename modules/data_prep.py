
import pandas as pd
import re
from math import radians, sin, cos, asin, sqrt, floor, ceil  
from scipy.spatial.distance import cdist
import numpy as np 
import geojson
from datetime import datetime, timedelta
from modules.model import EarthquakeAnalyzer
import modules.data_prep as data_prep
from modules.config import GEOJSON_OF_FAULTS_PATH, DATE_INTERVAL, START_MONTH, START_YEAR, END_MONTH, END_YEAR, TUPLE_COLUMNS_TO_UNPACK



def extract_cities(df: pd.DataFrame) -> pd.DataFrame:
    """Extract city names from location column (text in parentheses at the end)"""
    def get_city(location):
        if '(' in location and ')' in location:
            start = location.rfind('(')
            end = location.rfind(')')
            if start < end:
                return location[start+1:end].strip()
        return None
    
    df['city'] = df['location'].apply(get_city)
    return df


def calculate_fault_coor_limits(data: pd.DataFrame) -> int:
    min_lat = floor(min(data['latitude']))
    max_lat = ceil(max(data['latitude']))
    min_lng = floor(min(data['longitude']))
    max_lng = ceil(max(data['longitude']))

    return min_lat, max_lat, min_lng, max_lng

def filter_features_by_bounds(features, min_lat, max_lat, min_lng, max_lng):
    """Filter GeoJSON features by coordinate bounding box"""
    filtered = []
    
    for feature in features:
        try:
            coords = feature['geometry']['coordinates']
            
            if feature['geometry']['type'] == 'Point':
                lng, lat = coords[0], coords[1]
                if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                    filtered.append(feature)
            
            elif feature['geometry']['type'] in ['LineString', 'MultiPoint']:
                for coord in coords:
                    lng, lat = coord[0], coord[1]
                    if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                        filtered.append(feature)
                        break
            
            elif feature['geometry']['type'] == 'Polygon':
                for ring in coords:
                    for coord in ring:
                        lng, lat = coord[0], coord[1]
                        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                            filtered.append(feature)
                            break
        
        except (ValueError, IndexError, TypeError):
            # Skip features with invalid geometry
            continue
    
    return filtered

def load_and_filter_faults(data: pd.DataFrame) -> pd.DataFrame:

    with open(GEOJSON_OF_FAULTS_PATH, encoding='utf-8') as f:
        gj = geojson.load(f)

    min_lat, max_lat, min_lng, max_lng = calculate_fault_coor_limits(data)
    filtered_features = filter_features_by_bounds(
        gj['features'],
        min_lat, max_lat,
        min_lng, max_lng
    )
    print(f"Total features: {len(gj['features'])}")
    print(f"Filtered features: {len(filtered_features)}")


    features_list = []
    for feature in filtered_features:
        row = feature.get('properties', {}).copy()
        row['geometry_type'] = feature['geometry']['type']
        
        # Add coordinates
        coords = feature['geometry']['coordinates']
        if feature['geometry']['type'] == 'Point':
            row['longitude'] = coords[0]
            row['latitude'] = coords[1]
        elif feature['geometry']['type'] in ['LineString', 'MultiPoint']:
            row['coordinates'] = coords
        elif feature['geometry']['type'] == 'Polygon':
            row['coordinates'] = coords
        
        features_list.append(row)

    features_df = pd.DataFrame(features_list)
    
    return features_df, filtered_features, gj


def find_closest_fault(earthquake_lat, earthquake_lng, faults_df):
    """Find closest fault line to an earthquake"""
    try:

        fault_coords = []
        for coords in faults_df['coordinates']:
            if isinstance(coords, list) and len(coords) > 0:

                if isinstance(coords[0], list):
                    fault_coords.append(coords[0][:2])
                else:
                    fault_coords.append(coords[:2])
        
        if not fault_coords:
            return None, float('inf')
        

        distances = cdist(
            [[earthquake_lng, earthquake_lat]], 
            fault_coords
        )[0]
        
        closest_idx = np.argmin(distances)
        return closest_idx, distances[closest_idx]
    
    except Exception:
        return None, float('inf')
    
    

def calculate_distance_by_m_and_km(features_df: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    def haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000.0
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi/2.0)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2.0)**2
        return 2 * R * asin(sqrt(a))

    def _first_coord(coords):
        if coords is None:
            return None
        if isinstance(coords, (list, tuple)) and len(coords) >= 2 and isinstance(coords[0], (int, float)):
            return coords[:2]
        if isinstance(coords, (list, tuple)) and len(coords) > 0:
            return _first_coord(coords[0])
        return None

    # Build lookup: index -> (lat, lon)
    fault_point_lookup = {}
    for idx, row in features_df.iterrows():
        coords = row.get('coordinates', None)
        first = _first_coord(coords)
        if first:
            fault_point_lookup[idx] = (first[1], first[0])  # lat, lon

    def compute_distance_to_fault_m(row):
        idx = row.get('closest_fault_idx', None)
        if pd.isna(idx):
            return np.nan
        try:
            idx = int(idx)
        except Exception:
            return np.nan
        pt = fault_point_lookup.get(idx)
        if not pt:
            return np.nan
        fault_lat, fault_lon = pt
        try:
            return haversine_m(float(row['latitude']), float(row['longitude']), fault_lat, fault_lon)
        except Exception:
            return np.nan

    data['distance_to_fault_m'] = data.apply(compute_distance_to_fault_m, axis=1)
    data['distance_to_fault_km'] = (data['distance_to_fault_m'] / 1000.0).round(2)
    return data



def match_faults_to_earthquakes(data: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
    
    data['closest_fault_idx'] = data.apply(
        lambda row: find_closest_fault(
            row['latitude'], 
            row['longitude'], 
            features_df
        )[0],
        axis=1
    )

    data['distance_to_fault'] = data.apply(
        lambda row: find_closest_fault(
            row['latitude'], 
            row['longitude'], 
            features_df
        )[1],
        axis=1
    )


    data = data.merge(
        features_df.reset_index().rename(columns={'index': 'closest_fault_idx'}),
        on='closest_fault_idx',
        how='left',

    )
    data = calculate_distance_by_m_and_km(features_df, data)
    return data

    




def filter_by_time(df: pd.DataFrame, start=None, end=None) -> pd.DataFrame:
    """
    Filter dataframe by timestamp.
    start / end can be datetime, date, or parseable string. If None -> open-ended.
    """
    df2 = df.copy()
    if 'timestamp_dt' not in df2.columns:
        df2['timestamp_dt'] = pd.to_datetime(df2['timestamp'], errors='coerce')
    mask = pd.Series(True, index=df2.index)
    if start is not None:
        start_ts = pd.to_datetime(start)
        mask &= df2['timestamp_dt'] >= start_ts
    if end is not None:
        end_ts = pd.to_datetime(end)
        mask &= df2['timestamp_dt'] <= end_ts
    return df2[mask]


def unpack_tuple_for_most_likely_value(data, column_name):
    def parse_tuple(x):
        if isinstance(x, (tuple, list)):
            return x

        if isinstance(x, str):

            nums = re.findall(r"[-+]?\d*\.\d+|\d+", x)
            if len(nums) == 0:
                return None
            return tuple(float(n) for n in nums)
        
        return x  

    def extract_first(x):
        if isinstance(x, (tuple, list)):
            if len(x) == 0 or all(v is None for v in x):
                return np.nan
            return x[0]
        return x


    data[column_name] = data[column_name].apply(parse_tuple).apply(extract_first)
    return data

def re_filter_data_by_date_interval(data: pd.DataFrame, DATE_INTERVAL=DATE_INTERVAL) -> pd.DataFrame:
    if DATE_INTERVAL == 'LAST_2_DAYS':
        today = datetime.now()
        day_before = today - timedelta(days=1)
        today = str(today)[:-16]
        day_before = str(day_before)[:-16]

        filtered_data = filter_by_time(data, start='2025-11-18', end='2025-11-19')
        return filtered_data
    elif DATE_INTERVAL == 'FULL_DATASET':
        return data
    


def data_prep_pipeline():
    analyzer = EarthquakeAnalyzer(download_path="./earthquake_data")
    files = analyzer.query_period(start_year=START_YEAR, start_month=START_MONTH, end_year=END_YEAR, end_month=END_MONTH)
    data = analyzer.extract_data(files)
    data = data_prep.extract_cities(data)
    features_df, filtered_features, gj = data_prep.load_and_filter_faults(data)
    data = data_prep.match_faults_to_earthquakes(data, features_df)
    data['timestamp_dt'] = pd.to_datetime(data['timestamp'], errors='coerce')
    data = data_prep.calculate_distance_by_m_and_km(features_df, data)
    for col in TUPLE_COLUMNS_TO_UNPACK:
        data = data_prep.unpack_tuple_for_most_likely_value(data, col)

    return data, filtered_features, gj

