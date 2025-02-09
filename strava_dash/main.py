import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import plotly.express as px
from datetime import datetime
import pandas as pd

from strava_dash.func import columns_short, columns_shorter
from strava_dash.func import (
    get_engine,
    fetch_data,
    convert_units,
    generate_folium_map,
)

# TODO general: parts may be split up and put in other files (too much)


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


# NOTE OBJECT FOR TAB ACTIVITIES
# Creating df for all individual activities
activities["start_date"] = pd.to_datetime(activities["start_date"])
activities = activities.sort_values("start_date", ascending=False)
activities_ready = convert_units(
    activities[columns_shorter]
)  # TODO may need some rephrasing in output

# NOTE OBJECT FOR TAB HEATMAP
# Creating heatmap
generate_folium_map(activities)

# NOTE OBJECT FOR TAB OVERVIEW
# Creating line graph of cumulative distance per year
activities_ready["start_year"] = activities_ready["start_date"].dt.year
activities_ready["annual_cumulative_distance"] = (
    activities_ready.sort_values("start_date")
    .groupby("start_year")["distance"]
    .cumsum()
)

# Get current year and aimed distance goal
current_year = datetime.now().year
start_date = pd.to_datetime(f"{current_year}-01-01")
end_date = pd.to_datetime(f"{current_year}-12-31")
days_in_year = (end_date - start_date).days + 1

# Define the distance goal
total_goal_distance = 8000  # TODO Hardcoded
daily_distance_goal = total_goal_distance / days_in_year  # km/day
goal_dates = pd.date_range(start_date, end_date, freq="D")
goal_distances = daily_distance_goal * (goal_dates - start_date).days


fig_annual_cumsum = px.line(
    activities_ready.query("start_year == @current_year"),
    x="start_date",  # Adjust column name if needed
    y="annual_cumulative_distance",
    # color="start_year",  # Adjust this to a numeric column you want to plot
    # title=f"Cumulate km of rides for {current_year}",
)

fig_annual_cumsum.update_layout(
    xaxis=dict(
        range=[start_date, end_date],  # Full year range on x-axis
        tickformat="%b",  # Show month abbreviations on the x-axis
        tickmode="array",  # Specify custom ticks
        tickvals=pd.date_range(
            start=start_date, end=end_date, freq="MS"
        ),  # First of every month
        ticktext=[
            date.strftime("%b")
            for date in pd.date_range(start=start_date, end=end_date, freq="MS")
        ],  # Month names
    ),
    yaxis=dict(title="Cumulative Distance (km)"),
)

fig_annual_cumsum.add_scatter(
    x=goal_dates,  # The date range for the goal
    y=goal_distances,  # The cumulative goal distance
    mode="lines",
    name=f"Reference line for annual aim ({total_goal_distance} km)",  # Label for the goal line
    line=dict(color="grey", dash="dash"),  # Customize the line style (red, dashed)
)

# Creating df of annual summaries
annual_summaries = activities.groupby(activities["start_date"].dt.to_period("Y")).agg(
    n_activities=("resource_state", "size"),
    total_distance=("distance", "sum"),
    total_moving_time=("moving_time", "sum"),
    total_elapsed_time=("elapsed_time", "sum"),
    total_elevation_gain=("total_elevation_gain", "sum"),
    max_speed=("max_speed", "max"),
    average_speed=("average_speed", "mean"),
)

annual_summaries["average_speed_weighted"] = activities.groupby(
    activities["start_date"].dt.to_period("Y")
).apply(lambda x: (x["average_speed"] * x["distance"]).sum() / x["distance"].sum())

annual_summaries = convert_units(annual_summaries)
annual_summaries = annual_summaries.reset_index(drop=False)
annual_summaries["start_date"] = annual_summaries["start_date"].astype(str).astype(int)
annual_summaries_ready = annual_summaries.sort_values("start_date", ascending=False)

# NOTE Initialize the Dash app
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
                                    value="overview",
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
                    id="table_activities",
                    columns=[{"name": i, "id": i} for i in activities_ready.columns],
                    data=activities_ready.to_dict("records"),
                    style_table={"width": "100%", "margin": "auto"},
                    style_cell={"textAlign": "right"},
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
                dcc.Graph(
                    id="annual_summary_graph",
                    figure=fig_annual_cumsum,
                    style={"width": "100%", "height": "400px"},
                ),
                dash_table.DataTable(
                    id="table_annual_summaries",
                    columns=[
                        {"name": i, "id": i} for i in annual_summaries_ready.columns
                    ],
                    data=annual_summaries_ready.to_dict("records"),
                    style_table={"width": "100%", "margin": "auto"},
                    style_cell={"textAlign": "right"},
                    style_header={"fontWeight": "bold"},
                    # Enable sorting, filtering, and pagination
                    sort_action="native",
                    filter_action="native",
                    page_action="native",
                    page_size=100,  # Show 5 rows per page
                ),
            ]
        )


# Run the app
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
