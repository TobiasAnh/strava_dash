from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import numpy as np
import pandas as pd
import ast
import polyline
import plotly.graph_objects as go
import folium

columns_shorter = [
    "start_date",
    "activities_type",
    "name",
    "distance",
    "moving_time",
    "elapsed_time",
    "total_elevation_gain",
    "average_speed",
    "max_speed",
]

# Columns for dash
columns_short = [
    "name",
    "distance",
    "moving_time",
    "elapsed_time",
    "total_elevation_gain",
    "activities_type",
    "sport_type",
    "start_date",
    "start_date_local",
    "achievement_count",
    "kudos_count",
    "athlete_count",
    "photo_count",
    "start_latlng",
    "end_latlng",
    "average_speed",
    "max_speed",
    "average_cadence",
    "average_temp",
    "average_watts",
    "max_watts",
    "weighted_average_watts",
    "kilojoules",
    "elev_high",
    "elev_low",
    "pr_count",
    "total_photo_count",
    "map_id",
    "summary_polyline",
]


# Retrieve database credentials from environment variables
def get_engine():
    """
    Create and return a SQLAlchemy engine for a PostgreSQL database.
    Loads credentials from a .env file and builds the connection string.

    Returns:
        Engine: SQLAlchemy engine connected to the specified database.
    """
    if load_dotenv():
        DATABASE_USER = os.getenv("POSTGRES_USER")
        DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        DATABASE_HOST = os.getenv("POSTGRES_HOST")
        DATABASE_PORT = os.getenv("POSTGRES_PORT")
        DATABASE_NAME = os.getenv("POSTGRES_DB")

    # Create the engine using the credentials from the .env file
    engine = create_engine(
        f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )

    return engine


# Function to fetch data from PostgreSQL
def fetch_data(engine, query, index_col=None):
    with engine.connect() as connection:
        df = pd.read_sql(query, connection, index_col=index_col)
    return df


def generate_folium_map(
    activities,
    file_name,
    legend_name,
    zoom_start,
    lat_lon="auto",
    marker_opacity=0.5,
):
    """
    Generate an interactive Folium map of activities. Plots activity routes
    from encoded polylines with sport-specific colors and adds a legend
    based on sport type.

    Parameters:
        activities (DataFrame): Activity data with 'summary_polyline' and
                                'sport_type' columns.
        lat_long (tuple): Tuple of latitude and longitude coordinates
        file_name (str): name of produced html file
        marker_opacity (float): opacity of marker used for heatmap
    """

    # Create a map centered over Heidelberg
    if lat_lon == "auto":

        latitudes = []
        longitudes = []
        for coords in ["start_latlng", "end_latlng"]:
            # Convert string to list and convert start coords
            activities[coords] = activities[coords].apply(ast.literal_eval)

            latitudes.append(activities[coords].apply(lambda x: x[0]).to_list())
            longitudes.append(activities[coords].apply(lambda x: x[1]).to_list())

        # Calculate mean
        average_lat = np.mean(latitudes)
        average_lon = np.mean(longitudes)
    else:
        average_lat, average_lon = lat_lon

    mymap = folium.Map(
        location=[average_lat, average_lon],
        zoom_start=zoom_start,
        tiles="CartoDB Positron",  # map style
    )

    # Dictionary to hold the colors and labels for the legend
    legend_items = {}

    for activity in activities.index:
        activity_data = activities.loc[activity]
        if not activity_data["summary_polyline"]:
            # print(f"No polyline found for {activity_data['name']}, {activity_data['start_date']}")
            continue

        activity_polyline = activity_data["summary_polyline"]
        coordinates = polyline.decode(activity_polyline)
        sport_type = activity_data["sport_type"]

        # Determine the color based on sport type
        if sport_type == "Ride":
            color = "#1f78b4"
            label = "Road bike"
        elif sport_type == "MountainBikeRide":
            color = "#ff7f00"
            label = "MTB"
        elif sport_type == "Hike":
            color = "#33a02c"
            label = sport_type
        elif sport_type == "VirtualRide":
            color = "#6a3d9a"
            label = sport_type
        else:
            color = "#e31a1c"
            label = "Other"

        # Add the color and label to our legend dictionary if it's not already there
        legend_items[label] = color

        # Add a PolyLine to connect the coordinates
        folium.PolyLine(
            coordinates, color=color, weight=2.5, opacity=marker_opacity
        ).add_to(mymap)

    # --- Create the custom legend HTML ---
    # We will build the legend dynamically based on the sport types found
    # in the data.

    legend_html_items = ""
    for label, color in legend_items.items():
        legend_html_items += f"""
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
              <div style="width: 20px; height: 10px; background-color: {color}; margin-right: 5px;"></div>
              {label}
            </div>
        """

    legend_html = f"""
     <div style="position: fixed; 
                 top: 10px; right: 10px; 
                 width: auto; height: auto; 
                 border: 2px solid grey; 
                 z-index:9999; font-size:14px;
                 background-color: white;
                 opacity: 0.9;">
       <div style="background-color: #f0f0f0; padding: 5px; text-align: center; font-weight: bold;">
         {legend_name}
       </div>
       <div style="padding: 10px;">
         {legend_html_items}
       </div>
     </div>
     """

    # Add the HTML legend to the map
    mymap.get_root().html.add_child(folium.Element(legend_html))

    # Save the map to an HTML file
    mymap.save(file_name)


def findColumns(df, search_term):
    found_columns = [col for col in df.columns if search_term in col]
    # print(f"Found {len(found_columns)} columns having {search_term} in name")
    return found_columns


def convert_units(df, rounding_digits=0):
    df = df.copy()

    # Convert distance from meters to kilometers and overwrite column
    distance_cols = findColumns(df, "distance")
    for distance_col in distance_cols:
        df[distance_col] = round(df[distance_col] / 1000, rounding_digits)

    # Convert moving_time (seconds) to timedelta and then to minutes, overwrite the column
    time_cols = findColumns(df, "time")
    for time_col in time_cols:
        df[time_col] = pd.to_timedelta(df[time_col], unit="s")
        df[time_col] = df[time_col].apply(
            lambda x: f"{x.components.days} days {x.components.hours:02}:{x.components.minutes:02}"
        )

    # Convert speed from m/s to km/h and overwrite the columns
    speed_cols = findColumns(df, "speed")
    for speed_col in speed_cols:
        df[speed_col] = round(df[speed_col] * 3.6, rounding_digits)

    # Rounding elevation gain
    df["total_elevation_gain"] = round(df["total_elevation_gain"], rounding_digits)

    return df
