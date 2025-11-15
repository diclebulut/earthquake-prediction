
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm


def generate_map(data, filtered_features, gj):
    faults_features = filtered_features if filtered_features else (gj.get('features', []) if gj else [])
    faults_fc = {'type': 'FeatureCollection', 'features': faults_features}

    if not data.empty and 'latitude' in data.columns and 'longitude' in data.columns:
        center = [data['latitude'].mean(), data['longitude'].mean()]
    else:
        center = [39.0, 35.0]

    m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')

    if faults_features:
        folium.GeoJson(
            faults_fc,
            name='Faults',
            style_function=lambda feat: {
                'color': 'black' if feat.get('geometry', {}).get('type') in ('LineString', 'MultiLineString') else 'darkred',
                'weight': 2,
                'opacity': 0.8
            },
            tooltip=folium.GeoJsonTooltip(fields=list(faults_features[0].get('properties', {}).keys()) if faults_features and faults_features[0].get('properties') else None)
        ).add_to(m)

    if 'magnitude' in data.columns and not data['magnitude'].isna().all():
        mag_min, mag_max = float(data['magnitude'].min()), float(data['magnitude'].max())
    else:
        mag_min, mag_max = 0.0, 9.0
    cmap = cm.linear.YlOrRd_09.scale(mag_min, mag_max)

    marker_cluster = MarkerCluster(name='Earthquakes').add_to(m)
    for _, row in data.iterrows():
        try:
            lat = float(row['latitude'])
            lng = float(row['longitude'])
        except Exception:
            continue
        mag = row.get('magnitude', None)
        mag_val = float(mag) if mag not in (None, '') else None
        color = cmap(mag_val) if mag_val is not None else '#3186cc'
        radius = max(3, 2 + (mag_val if mag_val is not None else 0) * 2)
        popup_html = (
            f"<b>Magnitude:</b> {mag}<br>"
            f"<b>Location:</b> {row.get('location', '')}<br>"
            f"<b>City:</b> {row.get('city', '')}<br>"
            f"<b>Time:</b> {row.get('timestamp', '')}<br>"
            f"<b>Distance to fault (km):</b> {row.get('distance_to_fault_km', '')}<br>"
            f"<b>Closest fault ID:</b> {row.get('catalog_id', '')}"
        )
        folium.CircleMarker(
            location=[lat, lng],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(marker_cluster)

        
        if mag_val and mag_val > 3.5:
            folium.Marker(
                location=[lat, lng],
                icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa'),
                tooltip=f"High Magnitude: {mag_val}"
            ).add_to(m)


    cmap.caption = 'Earthquake magnitude'
    cmap.add_to(m)
    folium.LayerControl().add_to(m)

    return m