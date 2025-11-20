import json
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

# --- 1. Custom Web Page (To catch JS errors) ---
class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceId):
        # Useful for debugging Leaflet errors
        print(f"JS Console ({sourceId}:{lineNumber}): {message}")


# --- 2. Custom View (To control zooming behavior) ---
class ZoomableWebEngineView(QWebEngineView):
    def wheelEvent(self, event):
        # Ignore wheel events so the map doesn't zoom when you are 
        # just trying to scroll down the dashboard page.
        event.ignore()


# --- 3. Map Widget (The Container) ---
class MapWidget(QWidget):
    def __init__(self, is_fleet_map=False):
        super().__init__()
        self.is_fleet_map = is_fleet_map
        self.setObjectName("card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.webview = ZoomableWebEngineView()
        self.webview.setPage(WebEnginePage(self))
        
        # Default Center: New Delhi
        self.webview.setHtml(self.get_map_html(28.6139, 77.2090))
        
        # Transparent background for better UI integration
        self.webview.page().setBackgroundColor(Qt.transparent)
        layout.addWidget(self.webview)

    def get_map_html(self, lat, lng):
        """
        Returns the HTML/JS string for the Leaflet Map.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Map</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <style>
                body {{ margin:0; padding:0; background-color: transparent; }} 
                #map {{ height: 100vh; width: 100%; border-radius: 16px; }}
                .leaflet-control-layers {{
                    background: #1F1F1F;
                    color: #E0E0E0;
                    border: 1px solid #333;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // 1. Define Layers
                var darkLayer = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; OpenStreetMap'
                }});
                var satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                    attribution: 'Tiles &copy; Esri'
                }});

                // 2. Init Map
                var map = L.map('map', {{
                    center: [{lat}, {lng}],
                    zoom: 15,
                    zoomControl: true,
                    layers: [satLayer] 
                }});

                // 3. Layer Control
                var baseMaps = {{ "Satellite": satLayer, "Dark Mode": darkLayer }};
                L.control.layers(baseMaps).addTo(map);

                // 4. DEFINE HAZARD ZONE (Hidden by default)
                var hazardZone = L.circle([{lat}, {lng}], {{
                    color: '#ef4444',        
                    fillColor: '#ef4444',    
                    fillOpacity: 0.3,       
                    radius: 400              
                }});
                
                hazardZone.bindPopup("⚠️ HIGH GAS DETECTED HERE");

                var markerLayer = L.layerGroup().addTo(map);

                var redIcon = new L.Icon({{
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                }});
            </script>
        </body>
        </html>
        """

    def update_marker(self, lat, lng, gas_level, threshold):
        """
        Updates the single marker position and toggles the red 'Hazard Zone' circle.
        """
        js_code = f"""
        if (typeof map !== 'undefined') {{
            var newLatLng = new L.LatLng({lat}, {lng});
            
            // 1. Update Marker Position
            if (typeof activeMarker === 'undefined') {{
                activeMarker = L.marker(newLatLng, {{icon: redIcon}}).addTo(markerLayer);
            }} else {{
                activeMarker.setLatLng(newLatLng);
            }}
            
            map.panTo(newLatLng);

            // 2. DYNAMIC GEOFENCE LOGIC
            if ({gas_level} > {threshold}) {{
                if (!map.hasLayer(hazardZone)) {{
                    // Update circle position to current user location
                    hazardZone.setLatLng(newLatLng); 
                    map.addLayer(hazardZone);
                }} else {{
                    hazardZone.setLatLng(newLatLng);
                }}
            }} else {{
                if (map.hasLayer(hazardZone)) {{
                    map.removeLayer(hazardZone);
                }}
            }}
        }}
        """
        self.webview.page().runJavaScript(js_code)

    def update_all_markers(self, helmets_data):
        """
        Used for the 'Fleet Map' page to show multiple helmets at once.
        """
        if not helmets_data:
            return

        # Prepare the data structure for JavaScript
        helmets_json = json.dumps([
            {"id": hel_id, "lat": data[-1]['latitude'], "lng": data[-1]['longitude']} 
            for hel_id, data in helmets_data.items() if data
        ])

        # Formatted JavaScript Code
        js_code = f"""
        if (typeof map !== 'undefined' && typeof markerLayer !== 'undefined') {{
            // 1. Clear old markers
            markerLayer.clearLayers();
            
            // 2. Get data from Python
            var helmets = {helmets_json};
            
            // 3. Loop through helmets and add markers
            helmets.forEach(function(helmet) {{
                var marker = L.marker([helmet.lat, helmet.lng], {{icon: redIcon}});
                
                // Add text label (Helmet ID) above marker
                marker.bindTooltip(helmet.id, {{ 
                    permanent: true, 
                    direction: 'top', 
                    offset: [0, -10] 
                }});
                
                markerLayer.addLayer(marker);
            }});
        }}
        """
        self.webview.page().runJavaScript(js_code)