import requests
import json
import folium
import time
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from threading import Thread
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Create a map centered around London, Ontario
def create_map():
    return folium.Map(location=[42.9836, -81.2497], zoom_start=13)

# Fetch and update bus locations
def update_bus_locations():
    url = "http://gtfs.ltconline.ca/Vehicle/VehiclePositions.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        vehicle_data = response.json()
        # Create a new map for each update
        m = create_map()
        
        # Add markers for each bus
        for entity in vehicle_data.get("entity", []):
            vehicle = entity.get("vehicle", {})
            vehicle_id = vehicle.get("vehicle", {}).get("id")
            position = vehicle.get("position", {})
            latitude = position.get('latitude')
            longitude = position.get('longitude')
            
            if latitude and longitude:
                folium.Marker(
                    location=[latitude, longitude],
                    popup=f"Vehicle ID: {vehicle_id}",
                    icon=folium.Icon(color="blue", icon="cloud")
                ).add_to(m)

        # Save map in the static folder
        m.save(os.path.join('static', 'live_bus_map.html'))
        print("Map updated.")
        
        # Emit the update to the client
        socketio.emit('update_map')

# Set up a background thread to update the map every 1 seconds
def background_update():
    while True:
        update_bus_locations()
        time.sleep(1)  # Update every 1 seconds

# Route for rendering the map in the browser
@app.route("/")
def index():
    # Serve the map file from the static directory
    return send_from_directory('static', 'live_bus_map.html')

if __name__ == "__main__":
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Start the background update in a separate thread
    Thread(target=background_update, daemon=True).start()
    socketio.run(app, debug=True)
