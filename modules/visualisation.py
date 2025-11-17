import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
from branca.element import Template, MacroElement
from collections import Counter
import json

def generate_map(data, filtered_features, gj, high_mag_threshold):
    faults_features = filtered_features if filtered_features else (gj.get('features', []) if gj else [])

    if not data.empty and 'latitude' in data.columns and 'longitude' in data.columns:
        center = [data['latitude'].mean(), data['longitude'].mean()]
    else:
        center = [39.0, 35.0]

    m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')

    def fault_style(feat):
        return {
            'color': 'black' if feat.get('geometry', {}).get('type') in ('LineString', 'MultiLineString') else 'darkred',
            'weight': 2,
            'opacity': 0.8
        }

    faults_by_catalog = {}
    for feat in faults_features:
        props = feat.get('properties', {}) if isinstance(feat, dict) else {}
        catalog = props.get('catalog_id') or props.get('id') or props.get('catalogId') or props.get('catalog') or 'unknown'
        catalog = str(catalog)
        faults_by_catalog.setdefault(catalog, []).append(feat)

    cat_counter = Counter()
    if 'catalog_id' in data.columns:
        for val in data['catalog_id'].fillna('').astype(str):
            if val:
                cat_counter[val] += 1
    if not cat_counter and 'closest_fault_id' in data.columns:
        for val in data['closest_fault_id'].fillna('').astype(str):
            if val:
                cat_counter[val] += 1

    catalog_layers = []  
    for catalog, feats in faults_by_catalog.items():
        fc = {'type': 'FeatureCollection', 'features': feats}
        fg = folium.FeatureGroup(name=f"Faults catalog {catalog}", show=False)
        geo = folium.GeoJson(fc, name=f"faults_{catalog}", style_function=fault_style,
                             tooltip=folium.GeoJsonTooltip(fields=list(feats[0].get('properties', {}).keys()) if feats and feats[0].get('properties') else None))
        geo.add_to(fg)
        fg.add_to(m)
        catalog_layers.append({
            'catalog': catalog,
            'count': int(cat_counter.get(catalog, 0)),
            'fg_name': fg.get_name(),
            'geo_name': geo.get_name()
        })

    if 'magnitude' in data.columns and not data['magnitude'].isna().all():
        mag_min, mag_max = float(data['magnitude'].min()), float(data['magnitude'].max())
    else:
        mag_min, mag_max = 0.0, 9.0
    cmap = cm.linear.YlOrRd_09.scale(mag_min, mag_max)

    mag_bins = [
        (0.0, 1.0, '0 < mag <= 1'),
        (1.0, 2.0, '1 < mag <= 2'),
        (2.0, 3.0, '2 < mag <= 3'),
        (3.0, 4.0, '3 < mag <= 4'),
        (4.0, 10.0, 'mag > 4')
    ]
    bin_groups = {}
    for _, _, label in mag_bins:
        fg = folium.FeatureGroup(name=label, show=True)
        fg.add_to(m)
        bin_groups[label] = fg

    clusters = {label: MarkerCluster(name=f"Cluster {label}").add_to(bin_groups[label]) for label in bin_groups}

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

        bin_label = None
        if mag_val is None:
            bin_label = list(bin_groups.keys())[0]
        else:
            for low, high, label in mag_bins:
                if low < mag_val <= high or (label == 'mag > 4' and mag_val > 4.0):
                    bin_label = label
                    break
            if bin_label is None:
                bin_label = list(bin_groups.keys())[-1]

        folium.CircleMarker(
            location=[lat, lng],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(clusters[bin_label])

        if mag_val and mag_val > high_mag_threshold:
            folium.Marker(
                location=[lat, lng],
                icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa'),
                tooltip=f"High Magnitude: {mag_val}"
            ).add_to(m)

    cmap.caption = 'Earthquake magnitude'
    cmap.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    if catalog_layers:
        map_name = m.get_name()
        display_list = sorted(catalog_layers, key=lambda x: -x['count'])

        js_layers_json = json.dumps(display_list)

        template_html = f"""
        <style>
          .catalog-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            background: white;
            padding: 8px;
            border-radius: 4px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            max-height: 340px;
            overflow: auto;
            font-family: Arial, sans-serif;
            font-size: 13px;
            width: 220px;
          }}
          .catalog-panel h4 {{ margin: 0 0 6px 0; font-size: 14px; }}
          .catalog-panel ul {{ list-style: none; padding: 0; margin: 0; }}
          .catalog-panel li.item {{ display:flex; align-items:center; justify-content:space-between; padding:4px 0; border-bottom: 1px solid #f0f0f0; }}
          .catalog-panel li.item .label {{ cursor:pointer; flex:1; padding-right:6px; }}
          .catalog-panel li.item:hover {{ background:#fff; }}
          .catalog-panel .count {{ color:#666; font-size:12px; margin-left:6px; }}
        </style>
        <div class="catalog-panel">
          <h4>Fault catalog_ids</h4>
          <ul id="catalog-list">
          </ul>
          <div style="margin-top:6px; font-size:11px; color:#666">Toggle to view faults. Click label to highlight.</div>
        </div>

        <script>
        (function() {{
            var map = {map_name};
            var layers = {js_layers_json};

            function addList() {{
                var ul = document.getElementById('catalog-list');
                layers.forEach(function(it) {{
                    var li = document.createElement('li');
                    li.className = 'item';
                    var chk = document.createElement('input');
                    chk.type = 'checkbox';
                    chk.dataset.fg = it.fg_name;
                    chk.dataset.geo = it.geo_name;
                    chk.id = 'chk_' + it.catalog;
                    chk.onchange = function(e) {{
                        try {{
                            var fg = window[this.dataset.fg];
                            if(this.checked) {{
                                map.addLayer(fg);
                            }} else {{
                                map.removeLayer(fg);
                            }}
                        }} catch(err){{ console.warn(err); }}
                    }};
                    var lbl = document.createElement('span');
                    lbl.className = 'label';
                    lbl.textContent = it.catalog + ' (' + it.count + ')';
                    lbl.style.cursor = 'pointer';
                    lbl.onclick = function() {{
                        // reset style of all catalog geo layers
                        layers.forEach(function(x) {{
                            try {{
                                var g = window[x.geo_name];
                                if(g && g.resetStyle) g.resetStyle();
                            }} catch(e){{}}
                        }});
                        // highlight this catalog
                        try {{
                            var geo = window[it.geo_name];
                            if(geo) {{
                                geo.eachLayer(function(l) {{
                                    if(l.setStyle) l.setStyle({{color:'yellow', weight:4, opacity:1}});
                                }});
                                try {{ map.fitBounds(geo.getBounds(), {{padding:[20,20]}}); }} catch(e){{}}
                            }}
                        }} catch(e){{ console.warn(e); }}
                    }};
                    li.appendChild(chk);
                    li.appendChild(lbl);
                    ul.appendChild(li);
                }});
            }}

            // add list after a short timeout so folium has injected vars
            setTimeout(addList, 200);
        }})();
        </script>
        """

        macro = MacroElement()
        macro._template = Template(template_html)
        m.get_root().add_child(macro)

    return m






def generate_basic_map(data, filtered_features, gj, high_mag_threshold):
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

        
        if mag_val and mag_val > high_mag_threshold:
            folium.Marker(
                location=[lat, lng],
                icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa'),
                tooltip=f"High Magnitude: {mag_val}"
            ).add_to(m)


    cmap.caption = 'Earthquake magnitude'
    cmap.add_to(m)
    folium.LayerControl().add_to(m)

    return m



import ipywidgets
from IPython.display import display

def generate_alt_map(data, filtered_features, gj, high_mag_threshold, return_widgets=False):
    """
    Build a folium.Map (not displayed) and optionally return widgets for interactive use in a notebook.

    - If return_widgets is False (default) returns a folium.Map object (saveable via map.save(...) or converted to XML/HTML).
    - If return_widgets is True returns a dict: {'map': folium.Map, 'dropdown': ipywidget.Dropdown, 'out_widget': ipywidgets.Output, 'build_map': callable}
      so the caller can display widgets in a notebook and still obtain the map later.
    """
    faults_features = filtered_features if filtered_features else (gj.get('features', []) if gj else [])

    faults_by_catalog = {}
    for feat in faults_features:
        props = feat.get('properties', {}) if isinstance(feat, dict) else {}
        catalog = props.get('catalog_id') or props.get('id') or props.get('catalogId') or props.get('catalog') or 'unknown'
        catalog = str(catalog)
        faults_by_catalog.setdefault(catalog, []).append(feat)

    def build_map(selected_catalog='All'):
        if not data.empty and 'latitude' in data.columns and 'longitude' in data.columns:
            center = [data['latitude'].mean(), data['longitude'].mean()]
        else:
            center = [39.0, 35.0]

        m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')

        cat_counter = Counter()
        if 'catalog_id' in data.columns:
            for val in data['catalog_id'].fillna('').astype(str):
                if val:
                    cat_counter[val] += 1
        if not cat_counter and 'closest_fault_id' in data.columns:
            for val in data['closest_fault_id'].fillna('').astype(str):
                if val:
                    cat_counter[val] += 1

        counts = [int(cat_counter.get(c, 0)) for c in faults_by_catalog.keys()]
        if counts:
            cnt_min, cnt_max = min(counts), max(counts)
            if cnt_min == cnt_max:
                cnt_min = 0
            cmap_counts = cm.linear.YlGnBu_09.scale(cnt_min, cnt_max if cnt_max > cnt_min else cnt_min + 1)
        else:
            cmap_counts = cm.linear.YlGnBu_09.scale(0, 1)

        for catalog, feats in faults_by_catalog.items():
            if selected_catalog != 'All' and selected_catalog != catalog:
                continue

            fc = {'type': 'FeatureCollection', 'features': feats}
            count_for_catalog = int(cat_counter.get(catalog, 0))

            def style_func(feat, cnt=count_for_catalog):
                geom_type = feat.get('geometry', {}).get('type')
                color = cmap_counts(cnt) if cnt is not None else '#000000'
                weight = 2 + min(cnt, 20) * 0.2
                return {
                    'color': color,
                    'weight': weight,
                    'opacity': 0.9 if geom_type in ('LineString', 'MultiLineString') else 0.8
                }

            fg = folium.FeatureGroup(name=f"Faults catalog {catalog}", show=True)
            geo = folium.GeoJson(
                fc,
                name=f"faults_{catalog}",
                style_function=style_func,
                tooltip=folium.GeoJsonTooltip(fields=list(feats[0].get('properties', {}).keys()) if feats and feats[0].get('properties') else None)
            )
            geo.add_to(fg)
            fg.add_to(m)

        if 'magnitude' in data.columns and not data['magnitude'].isna().all():
            mag_min, mag_max = float(data['magnitude'].min()), float(data['magnitude'].max())
        else:
            mag_min, mag_max = 0.0, 9.0
        cmap = cm.linear.YlOrRd_09.scale(mag_min, mag_max)

        mag_bins = [
            (0.0, 1.0, '0 < mag <= 1'),
            (1.0, 2.0, '1 < mag <= 2'),
            (2.0, 3.0, '2 < mag <= 3'),
            (3.0, 4.0, '3 < mag <= 4'),
            (4.0, 10.0, 'mag > 4')
        ]
        bin_groups = {}
        for _, _, label in mag_bins:
            fg = folium.FeatureGroup(name=label, show=True)
            fg.add_to(m)
            bin_groups[label] = fg

        clusters = {label: MarkerCluster(name=f"Cluster {label}").add_to(bin_groups[label]) for label in bin_groups}

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

            bin_label = None
            if mag_val is None:
                bin_label = list(bin_groups.keys())[0]
            else:
                for low, high, label in mag_bins:
                    if low < mag_val <= high or (label == 'mag > 4' and mag_val > 4.0):
                        bin_label = label
                        break
                if bin_label is None:
                    bin_label = list(bin_groups.keys())[-1]

            folium.CircleMarker(
                location=[lat, lng],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(clusters[bin_label])

            if mag_val and mag_val > high_mag_threshold:
                folium.Marker(
                    location=[lat, lng],
                    icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa'),
                    tooltip=f"High Magnitude: {mag_val}"
                ).add_to(m)

        cmap.caption = 'Earthquake magnitude'
        cmap.add_to(m)
        folium.LayerControl(collapsed=False).add_to(m)

        return m

    if return_widgets:
        out_map = ipywidgets.Output(layout={'border': '1px solid black', 'height': '600px'})
        catalog_options = ['All'] + sorted(list(faults_by_catalog.keys()))
        fault_dropdown = ipywidgets.Dropdown(
            options=catalog_options,
            value='All',
            description='Fault Catalog:',
            disabled=False,
        )

        def _on_dropdown_change(change):
            out_map.clear_output()
            with out_map:
                display(build_map(fault_dropdown.value))

        fault_dropdown.observe(_on_dropdown_change, names='value')

        out_map.clear_output()
        with out_map:
            display(build_map('All'))

        return {
            'map': build_map('All'),
            'dropdown': fault_dropdown,
            'out_widget': out_map,
            'build_map': build_map
        }

    return build_map('All')
