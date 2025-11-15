import os
from datetime import datetime
import pandas as pd
import requests
from xml.etree import ElementTree as ET



class EarthquakeAnalyzer:
    def __init__(self, download_path: str = "./data5"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.mkdir(download_path)
    
    def query_period(self, start_year: int, start_month: int, end_year: int, end_month: int) -> list:
        """Download earthquake data for a specific period"""
        downloaded_files = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
       
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        for year in range(start_year, end_year + 1):
            start_m = start_month if year == start_year else 1
            end_m = end_month if year == end_year else 12
            
            for month in range(start_m, end_m + 1):
                file_name = os.path.join(self.download_path, f"{year}{month:02}.xml")
                
                
                is_current_month = (year == current_year and month == current_month)
                
                if os.path.exists(file_name) and not is_current_month:
                    print(f"✓ Already exists: {year}-{month:02}")
                    downloaded_files.append(file_name)
                    continue
                
                url = f"http://udim.koeri.boun.edu.tr/zeqmap/xmlt/{year}{month:02}.xml"
                
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    if len(response.content) < 100:
                        print(f"Warning:  {year}-{month:02}: Empty response")
                        continue
                    
                    with open(file_name, "wb") as f:
                        f.write(response.content)
                    
                    downloaded_files.append(file_name)
                    status = "Downloaded" if not os.path.exists(file_name) else "Refreshed"
                    print(f"✓ {status}: {year}-{month:02}")
                    
                except Exception as e:
                    print(f"✗ Error {year}-{month:02}: {e}")
        
        return downloaded_files
        
    def extract_data(self, file_paths: list) -> dict:
        """Analyze earthquake data from XML files"""
        earthquakes = []
        
        for file_path in file_paths:
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                
                for event in root.findall("earhquake"):
                    magnitude = float(event.get("mag", 0))
                    latitude = float(event.get("lat", 0))
                    longitude = float(event.get("lng", 0))
                    depth = float(event.get("Depth", 0))
                    timestamp = event.get("name", "")
                    location = event.get("lokasyon", "").strip()
                    
                    if magnitude > 0:
                        earthquakes.append({
                            "timestamp": timestamp,
                            "location": location,
                            "magnitude": magnitude,
                            "latitude": latitude,
                            "longitude": longitude,
                            "depth": depth
                        })
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        
        
        earthquakes = pd.DataFrame.from_dict(earthquakes)
        print(f"Total earthquakes: {len(earthquakes)}")
        return earthquakes