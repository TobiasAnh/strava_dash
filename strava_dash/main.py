import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd

from strava_dash.func import columns_short, columns_shorter
from strava_dash.func import (
    get_engine,
    fetch_data,
    get_all_polylines,
    get_density_fig,
    generate_folium_map,
)


# Connect to PostgreSQL database using SQLAlchemy
engine = get_engine()

# Load athlete
athlete_query = (
    "SELECT * FROM athlete"  # Replace 'your_table' with your actual table name
)

athlete = fetch_data(
    engine,
    athlete_query,
    index_col="athlete_id",
)

# Load activities
activities_query = (
    "SELECT * FROM activities"  # Replace 'your_table' with your actual table name
)

activities = fetch_data(
    engine,
    activities_query,
    "activity_id",
)

activities["start_date"] = pd.to_datetime(activities["start_date"]).dt.date
activities = activities.sort_values("start_date", ascending=False)

activities = activities[columns_short]
activities_short = activities[columns_shorter]

generate_folium_map()

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div(
    [
        html.H1(
            f"Strava activities of {athlete['firstname'].values}",
            style={"text-align": "center"},
        ),
        # Tab navigation
        html.Div(
            [
                dcc.Tabs(
                    id="tabs",
                    value="heatmap",
                    children=[
                        dcc.Tab(
                            label="Activities",
                            value="activities",
                            style={"width": "100%"},
                            # style={"padding": "10px"},
                        ),
                        dcc.Tab(
                            label="Heatmap",
                            value="heatmap",
                            style={"width": "100%"},
                            # style={"padding": "10px"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "width": "15%",
                        # "margin-right": "2%",
                    },
                ),
                # Content will be rendered in this Div based on the selected tab
                html.Div(id="tabs-content", style={"width": "80%"}),
            ],
            style={"display": "flex"},
        ),
    ]
)


# Callback to update content based on selected tab
@app.callback(
    dash.dependencies.Output("tabs-content", "children"),
    [dash.dependencies.Input("tabs", "value")],
)
def render_content(tab):
    if tab == "activities":
        # Content for the first tab
        return html.Div(
            [
                dash_table.DataTable(
                    id="table",
                    columns=[{"name": i, "id": i} for i in activities_short.columns],
                    data=activities_short.to_dict("records"),
                    style_table={"width": "70%", "margin": "auto"},
                    style_cell={"textAlign": "center"},
                    style_header={"fontWeight": "bold"},
                    # Enable sorting, filtering, and pagination
                    sort_action="native",
                    filter_action="native",
                    page_action="native",
                    page_size=20,  # Show 5 rows per page
                ),
            ]
        )
    elif tab == "heatmap":
        return html.Iframe(
            srcDoc=open("heatmap.html", "r").read(),  # Load the saved HTML file
            width="100%",  # Width of the map
            height="600",  # Height of the map
        )


# Run the app
if __name__ == "__main__":
    app.run_server(debug=False)
