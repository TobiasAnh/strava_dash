import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from datetime import datetime
import pandas as pd

from strava_dash.func import columns_short, columns_shorter
from strava_dash.func import (
    get_engine,
    fetch_data,
    convert_units,
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


###### TODO df and metrics for new overview tab
# Creating df for all individual activities
activities["start_date"] = pd.to_datetime(activities["start_date"])
activities = activities.sort_values("start_date", ascending=False)
activities_ready = convert_units(
    activities[columns_shorter]
)  # TODO may need some rephrasing in output

# Creating df of annul summaries
annual_summaries = activities.groupby(activities["start_date"].dt.to_period("Y")).agg(
    n_activities=("resource_state", "size"),
    total_distance=("distance", "sum"),
    total_moving_time=("moving_time", "sum"),
    total_elapsed_time=("elapsed_time", "sum"),
    total_elevation_gain=("total_elevation_gain", "sum"),
    average_speed=("average_speed", "mean"),  # TODO needs to be weighted by distance
    max_speed=("max_speed", "max"),
)

annual_summaries = convert_units(
    annual_summaries
)  # TODO convert units function not working for both dataframe yet
annual_summaries.sort_values()
#####

generate_folium_map(activities)

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=["/assets/bootstrap.min.css"],
)
server = app.server  # Expose the Flask server instance for WSGI servers

# Layout of the app
app.layout = html.Div(
    [
        dbc.Container(
            [
                dbc.Row(
                    dbc.Col(
                        html.H1(
                            f"Strava activities of {athlete['firstname'].values}",
                            style={"text-align": "center"},
                        ),
                        width={"size": 6, "offset": 3},
                    )
                ),
                dbc.Row(
                    dbc.Col(
                        html.Div(
                            [
                                dcc.Tabs(
                                    id="tabs",
                                    value="heatmap",
                                    children=[
                                        dcc.Tab(
                                            label="Overview",
                                            value="overview",
                                            style={"width": "50%"},
                                        ),
                                        dcc.Tab(
                                            label="Activities",
                                            value="activities",
                                            style={"width": "50%"},
                                        ),
                                        dcc.Tab(
                                            label="Heatmap",
                                            value="heatmap",
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flex-direction": "row",  # Horizontal tabs
                                        "width": "100%",
                                    },
                                ),
                                html.Div(id="tabs-content", style={"width": "100%"}),
                            ],
                        ),
                        width=12,  # Full width
                    )
                ),
            ],
            fluid=True,  # Improved responsiveness
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
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=activities.to_dict("records"),
                    style_table={"width": "100%", "margin": "auto"},
                    style_cell={"textAlign": "center"},
                    style_header={"fontWeight": "bold"},
                    # Enable sorting, filtering, and pagination
                    sort_action="native",
                    filter_action="native",
                    page_action="native",
                    page_size=100,  # Show 5 rows per page
                ),
            ]
        )
    elif tab == "heatmap":
        return html.Iframe(
            srcDoc=open("heatmap.html", "r").read(),  # Load the saved HTML file
            width="100%",  # Width of the map
            height="600",  # Height of the map
        )

    elif tab == "overview":
        # Placeholder content for the new tab
        return html.Div(
            [
                html.H3("This is a new tab!"),
                html.P("Content for this tab will be added later."),
            ],
            style={"textAlign": "center", "padding": "20px"},
        )


# Run the app
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
