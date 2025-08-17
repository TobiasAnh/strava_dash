# Strava Dash

A web dashboard built with [Dash](https://dash.plotly.com/) and [Plotly](https://plotly.com/python/) to visualize Strava activity data stored in a PostgreSQL database.  
The app provides interactive tables, graphs, and a heatmap of your activities.

---

## Features
- 📊 **Annual Progress**: Cumulative distance plot against yearly goal  
- 🗺️ **Heatmap**: Interactive Folium map of all activities  
- 📋 **Tables**: Sortable and filterable activity and annual summary tables  
- 🖥️ **Dashboard**: Responsive layout with tabs for **Overview**, **Activities**, and **Heatmap**

---

## Requirements
- Python 3.9+  
- PostgreSQL database with Strava data  


If running locally without Docker, install dependencies:
```bash
pip install -r requirements.txt


Environmental variables are loaded from .env file that needs to be created in the project root

POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=strava