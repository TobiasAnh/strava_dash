from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import pandas as pd
import polyline
import plotly.graph_objects as go
import folium

columns_shorter = [
    "start_date",
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


def generate_folium_map(activities):

    # Create a map centered at the average location
    average_lat = 49.37
    average_lon = 8.78

    mymap = folium.Map(
        location=[average_lat, average_lon],
        zoom_start=10,
        tiles="CartoDB Positron",
    )

    for activity in activities.index:
        activity = activities.loc[activity]
        if not activity["summary_polyline"]:
            # print(f"No polyline found for {activity['name']}, {activity['start_date']}")
            continue

        activity_polyline = activity["summary_polyline"]
        coordinates = polyline.decode(activity_polyline)

        if activity["sport_type"] == "Ride":
            color = "#1f78b4"
        elif activity["sport_type"] == "MountainBikeRide":
            color = "#ff7f00"
        elif activity["sport_type"] == "Hike":
            color = "#33a02c"
        elif activity["sport_type"] == "VirtualRide":
            color = "#6a3d9a"
        else:
            color = "#e31a1c"

        # Add a PolyLine to connect the coordinates
        folium.PolyLine(coordinates, color=color, weight=2.5, opacity=0.2).add_to(mymap)

    # Save the map to an HTML file
    mymap.save("heatmap.html")


def findColumns(df, search_term):
    found_columns = [col for col in df.columns if search_term in col]
    print(f"Found {len(found_columns)} columns having {search_term} in name")
    return found_columns


def convert_units(df):
    df = df.copy()

    # Convert distance from meters to kilometers and overwrite the column
    distance_cols = findColumns(df, "distance")
    for distance_col in distance_cols:
        df[distance_col] = round(df[distance_col] / 1000, 1)

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
        df[speed_col] = round(df[speed_col] * 3.6, 1)

    return df
