import polyline
import folium
from func import import_json

activities = import_json("activities.json")


# Create a map centered at the average location
average_lat = 49.37
average_lon = 8.78

mymap = folium.Map(location=[average_lat, average_lon], zoom_start=12)
for activity in activities:

    if not activity["map"]["summary_polyline"]:
        print(f"No polyline found for {activity['name']}, {activity['start_date']}")
        continue

    if activity["sport_type"] == "Ride":
        color = "blue"
    elif activity["sport_type"] == "MountainBikeRide":
        color = "red"
    elif activity["sport_type"] == "Hike":
        color = "yellow"
    elif activity["sport_type"] == "VirtualRide":
        color = "pink"
    else:
        color = "brown"

    activity_polyline = activity["map"]["summary_polyline"]
    coordinates = polyline.decode(activity_polyline)

    # Add a PolyLine to connect the coordinates
    folium.PolyLine(coordinates, color=color, weight=2.5, opacity=0.5).add_to(mymap)


# Save the map to an HTML file
heatmap_name = "heatmap.html"
mymap.save(heatmap_name)
