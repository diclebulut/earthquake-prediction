import pandas as pd
import folium
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
import os
from datetime import datetime
from modules.config import OUTPUT_DIR, OUTPUT_FAULT_STATS_DIR

def fault_stats_to_md_and_map(data, gj):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_name = f'{OUTPUT_DIR}/{OUTPUT_FAULT_STATS_DIR}'
    os.makedirs(folder_name, exist_ok=True)
    fault_activity = data.groupby('catalog_id').agg({
        'magnitude': ['count', 'mean', 'max', 'std'],
        'distance_to_fault_km': ['mean', 'min', 'max'],
        'depth': ['mean', 'std'],
        'slip_type': 'first',
        'net_slip_rate': 'first',
        'average_dip': 'first',
        'average_rake': 'first'
    }).round(2)

    fault_activity.columns = ['_'.join(col).strip() for col in fault_activity.columns]
    fault_activity = fault_activity.sort_values('magnitude_count', ascending=False).reset_index()

    top_faults = fault_activity.head(10)['catalog_id'].tolist()
    data['year_month'] = data['timestamp_dt'].dt.to_period('M')

    temporal_activity = data[data['catalog_id'].isin(top_faults)].groupby(
        ['catalog_id', 'year_month']
    ).agg({
        'magnitude': ['count', 'mean', 'max'],
        'distance_to_fault_km': 'mean'
    }).reset_index()

    temporal_activity.columns = ['_'.join(col).strip() if col[1] else col[0] for col in temporal_activity.columns]

    proximity_bins = [0, 5, 10, 25, 50]
    proximity_labels = ['0-5km', '5-10km', '10-25km', '25-50km']

    data['proximity_category'] = pd.cut(
        data['distance_to_fault_km'], 
        bins=proximity_bins, 
        labels=proximity_labels
    )

    proximity_analysis = data.groupby(['catalog_id', 'proximity_category']).agg({
        'magnitude': ['count', 'mean', 'max']
    }).reset_index()

    proximity_analysis.columns = ['_'.join(col).strip() if col[1] else col[0] for col in proximity_analysis.columns]

    fault_properties = data.groupby('catalog_id').agg({
        'magnitude': 'count',
        'slip_type': 'first',
        'net_slip_rate': 'first',
        'average_dip': 'first',
        'average_rake': 'first',
        'distance_to_fault_km': 'mean'
    }).rename(columns={'magnitude': 'earthquake_count'}).reset_index()

    summary_stats = pd.DataFrame({
        'Metric': [
            'Total Faults Analyzed',
            'Total Earthquakes',
            'Date Range Start',
            'Date Range End',
            'Average Distance to Fault (km)',
            'Median Distance to Fault (km)',
            'Min Distance to Fault (km)',
            'Max Distance to Fault (km)'
        ],
        'Value': [
            data['catalog_id'].nunique(),
            len(data),
            data['timestamp_dt'].min().strftime('%Y-%m-%d'),
            data['timestamp_dt'].max().strftime('%Y-%m-%d'),
            f"{data['distance_to_fault_km'].mean():.2f}",
            f"{data['distance_to_fault_km'].median():.2f}",
            f"{data['distance_to_fault_km'].min():.2f}",
            f"{data['distance_to_fault_km'].max():.2f}"
        ]
    })
    md_path = os.path.join(folder_name, f'fault_activity_analysis_{timestamp}.md')
    with open(md_path, 'w') as f:
        f.write("# Fault Activity Trend Analysis Report\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Summary Statistics\n\n")
        f.write(summary_stats.to_markdown(index=False))
        f.write("\n\n")
        f.write("## Top 10 Most Active Faults\n\n")
        f.write("### Earthquake Statistics\n\n")
        top_10_eq = fault_activity.head(10)[['catalog_id', 'magnitude_count', 'magnitude_mean', 'magnitude_max', 'magnitude_std']]
        f.write(top_10_eq.to_markdown(index=False))
        f.write("\n\n")
        f.write("### Distance Statistics\n\n")
        top_10_dist = fault_activity.head(10)[['catalog_id', 'distance_to_fault_km_mean', 'distance_to_fault_km_min', 'distance_to_fault_km_max', 'depth_mean', 'depth_std']]
        f.write(top_10_dist.to_markdown(index=False))
        f.write("\n\n")
        f.write("### Fault Properties\n\n")
        top_10_props = fault_activity.head(10)[['catalog_id', 'slip_type_first', 'net_slip_rate_first', 'average_dip_first', 'average_rake_first']]
        f.write(top_10_props.to_markdown(index=False))
        f.write("\n\n")
        f.write("## Active Fault Properties\n\n")
        props_summary = fault_properties.sort_values('earthquake_count', ascending=False).head(10)[['catalog_id', 'earthquake_count', 'slip_type', 'net_slip_rate', 'distance_to_fault_km']]
        f.write(props_summary.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Proximity Distribution for Top 5 Faults\n\n")
        for i, fault_id in enumerate(top_faults[:5], 1):
            fault_prox = proximity_analysis[proximity_analysis['catalog_id'] == fault_id].sort_values('magnitude_count', ascending=False)
            fault_info = fault_activity[fault_activity['catalog_id'] == fault_id].iloc[0]
            
            f.write(f"### #{i} Fault: {fault_id}\n\n")
            f.write(f"- **Total Earthquakes:** {int(fault_info['magnitude_count'])}\n")
            f.write(f"- **Avg Magnitude:** {fault_info['magnitude_mean']:.2f}\n")
            f.write(f"- **Max Magnitude:** {fault_info['magnitude_max']:.2f}\n")
            f.write(f"- **Slip Type:** {fault_info['slip_type_first']}\n")
            f.write(f"- **Net Slip Rate:** {fault_info['net_slip_rate_first']:.1f} mm/yr\n\n" if pd.notna(fault_info['net_slip_rate_first']) else "- **Net Slip Rate:** N/A\n\n")
            
            if len(fault_prox) > 0:
                f.write("**Earthquake Distribution by Distance:**\n\n")
                f.write(fault_prox[['proximity_category', 'magnitude_count', 'magnitude_mean', 'magnitude_max']].to_markdown(index=False))
            f.write("\n\n")
        
        f.write("## Temporal Activity (Top 10 Faults)\n\n")
        f.write(temporal_activity.head(20).to_markdown(index=False))
        f.write("\n\n")

        top_20_faults = fault_activity.head(20)['catalog_id'].tolist()
        fault_counts = fault_activity.head(20)[['catalog_id', 'magnitude_count']].copy()
        fault_counts = fault_counts.set_index('catalog_id')['magnitude_count'].to_dict()
        max_count = max(fault_counts.values())
        min_count = min(fault_counts.values())

        colors = ['#d7301f', '#b30000', '#7f0000']  
        cmap = LinearSegmentedColormap.from_list('dark_reds', colors)
        m = folium.Map(
            location=[39.0, 35.0],
            zoom_start=6,
            tiles='OpenStreetMap'
        )

        for feature in gj['features']:
            fault_id = feature['properties']['catalog_id']
            
            if fault_id not in top_20_faults:
                continue

            count = fault_counts[fault_id]
            normalized = (count - min_count) / (max_count - min_count) if max_count != min_count else 0.5
            color = mcolors.rgb2hex(cmap(normalized))
            line_weight = 4 + (normalized * 6)  

            
            fault_info = fault_activity[fault_activity['catalog_id'] == fault_id].iloc[0]
            popup_text = f"""
            <b>Fault ID:</b> {fault_id}<br>
            <b>Earthquakes:</b> {int(count)}<br>
            <b>Avg Magnitude:</b> {fault_info['magnitude_mean']:.2f}<br>
            <b>Max Magnitude:</b> {fault_info['magnitude_max']:.2f}<br>
            <b>Slip Type:</b> {fault_info['slip_type_first']}<br>
            <b>Net Slip Rate:</b> {fault_info['net_slip_rate_first']} mm/yr<br>
            <b>Avg Distance:</b> {fault_info['distance_to_fault_km_mean']:.2f} km
            """

            folium.GeoJson(
                feature,
                style_function=lambda x, color=color: {
                    'color': color,
                    'weight': line_weight,
                    'opacity': 0.8
                },
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Fault ID: {fault_id} | {int(count)} earthquakes"
            ).add_to(m)

        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 220px; height: auto; 
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px; padding: 10px">
        <p style="margin:0; font-weight:bold; text-align:center;">Top 20 Most Active Faults</p>
        <p style="margin:5px 0; font-size:12px;">
        <span style="color: {mcolors.rgb2hex(cmap(1.0))};">━━</span> High Activity ({int(max_count)} events)<br>
        <span style="color: {mcolors.rgb2hex(cmap(0.5))};">━━</span> Medium Activity<br>
        <span style="color: {mcolors.rgb2hex(cmap(0.0))};">━━</span> Lower Activity ({int(min_count)} events)
        </p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        map_path = os.path.join(folder_name, f'top_20_active_faults_map_{timestamp}.html')
        m.save(map_path)