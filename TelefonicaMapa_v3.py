# Dataset Telefónica
# María José Vota, Eugenia Rendón, Alan Velasco, Martha Elena García

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly as py
import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly import tools
from datetime import datetime as dt

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Initialize data frame
df = pd.read_csv("DataSet_Telefonica.csv")
# eliminar instancias con nulls (20)
df = df.dropna()


# convertir formato de fecha: string -> datetime
df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d")
# convertir formato de hora: float -> int
df["hora"] = df["hora"].astype(int)
# informacion sitio
sitios = df[["sitio", "latitud", "longitud"]].drop_duplicates()

# DataFrame agrupado por semana
grouped = df.groupby(["sitio", "tipo_plan", "tecnologia", "fecha"]).agg(
    {"sum_bytes": "sum"}
)
grouped = grouped.reset_index()
# grouped = grouped.set_index("fecha")
df_master = grouped.groupby(
    ["sitio", "tipo_plan", "tecnologia", pd.Grouper(key="fecha", freq="W-mon")]
).sum()
df_master = df_master.reset_index()
df_master = pd.merge(df_master, sitios, on="sitio", how="left")
df_master = df_master.reset_index()
df = df_master

# Diccionario de ubicaciones importantes en MTY
list_of_locations = {
    "Aeropuerto Internacional MTY": {"lat": 25.7728, "lon": -100.1079},
    "Parque Fundidora": {"lat": 25.6785, "lon": -100.2842},
    "Macroplaza": {"lat": 25.6692, "lon": -100.3099},
    "Paseo Santa Lucia": {"lat": 25.6707, "lon": -100.3059},
    "Cerro de la Silla": {"lat": 25.6320, "lon": -100.2332},
    "Parque la Huasteca": {"lat": 25.6494, "lon": -100.4510},
    "Parque Chipinque": {"lat": 25.6187, "lon": -100.3602},
    "Hospital Universitario": {"lat": 25.6887, "lon": -100.3501},
    "UDEM": {"lat": 25.6609, "lon": -100.4202},
    "Tec de MTY": {"lat": 25.6514, "lon": -100.2895},
}

## Mapa Dinámico de Radio Bases en Área Metropolitana

blackbold = {"color": "black", "font-weight": "bold"}

mapbox_access_token = "pk.eyJ1IjoibWFyaWFqb3NldnoiLCJhIjoiY2s5OTU1OXRqMDh6bDNubngxaWVyMmZ0aiJ9.2-Wv-0scEzITavhaqSrUcA"
app = dash.Dash(__name__)

# Layout of Dash app
app.layout = html.Div(
    children=[
        # Dash legend - checklists - map
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.Img(
                            className="logo",
                            src=app.get_asset_url("telefonica-logo.png"),
                        ),
                        html.H2("Análisis de Tráfico de consumo"),
                        html.P(
                            """Seleccione diversos días utilizando el selector de fechas 
                            seleccionando diferentes marcos de tiempo en el histograma."""
                        ),
                        # dropdown para fecha
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                dcc.DatePickerSingle(
                                    id="date-picker",
                                    min_date_allowed=dt(2019, 10, 4),
                                    max_date_allowed=dt(2019, 11, 5),
                                    initial_visible_month=dt(2019, 10, 4),
                                    display_format="MMMM D, YYYY",
                                    style={"border": "0px solid black"},
                                )
                            ],
                        ),
                        # dropdowns
                        # Change to side-by-side for mobile layout
                        html.Div(
                            className="row",
                            children=[
                                # Dropdown for locations on map
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        dcc.Dropdown(
                                            id="location-dropdown",
                                            options=[
                                                {"label": i, "value": i}
                                                for i in list_of_locations
                                            ],
                                            placeholder="Seleccione una ubicación",
                                        )
                                    ],
                                ),
                                # Dropdown tipo tecnologia
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        dcc.Dropdown(
                                            id="tech_name",
                                            options=[
                                                {"label": str(b), "value": b}
                                                for b in sorted(
                                                    df["tecnologia"].unique()
                                                )
                                            ],
                                            placeholder="Tipo de tecnología(s)",
                                        )
                                    ],
                                ),
                                # Dropdown tipo plan
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        dcc.Dropdown(
                                            id="tipo_plan",
                                            options=[
                                                {"label": str(b), "value": b}
                                                for b in sorted(
                                                    df["tipo_plan"].unique()
                                                )
                                            ],
                                            placeholder="Tipo de plan(es)",
                                        )
                                    ],
                                ),
                            ],
                        ),
                        # ultimas lineas
                        # html.P(id="total-rides"),
                        # html.P(id="total-rides-selection"),
                        # html.P(id="date-value"),
                        dcc.Markdown(children=["TEC de MTY, 2020"]),
                    ],
                ),
                # Mapa
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Graph(id="map-graph", style={"backgroundColor": "#343332"}),
                        html.Div(
                            className="text-padding",
                            children=[
                                "Seleccione cualquiera de las barras en el histograma "
                                "para seccionar los datos por tiempo."
                            ],
                        ),
                    ],
                ),
            ],
        )
    ],
)

# Output de la gráfica
@app.callback(
    Output("map-graph", "figure"),
    [
        Input("date-picker", "date"),
        Input("location-dropdown", "value"),
        Input("tech_name", "value"),
        Input("tipo_plan", "value"),
    ],
)
def update_figure(datePicked, selectedLocation, chosen_tech, chosen_plan):
    df_sub = df
    if datePicked is not None:
        df_sub = df_sub[df_sub["fecha"] == datePicked]
    if chosen_tech is not None:
        df_sub = df_sub[df_sub["tecnologia"] == chosen_tech]
    if chosen_plan is not None:
        df_sub = df_sub[df_sub["tipo_plan"] == chosen_plan]

    # Create figure
    locations = [
        go.Scattermapbox(
            lon=df_sub["longitud"],
            lat=df_sub["latitud"],
            marker=dict(
                showscale=True,
                # color=np.append(np.insert(listCoords.index.hour, 0, 0), 23),
                opacity=0.5,
                size=5,
                colorscale=[
                    [0, "#F4EC15"],
                    [0.04167, "#DAF017"],
                    [0.0833, "#BBEC19"],
                    [0.125, "#9DE81B"],
                    [0.1667, "#80E41D"],
                    [0.2083, "#66E01F"],
                    [0.25, "#4CDC20"],
                    [0.292, "#34D822"],
                    [0.333, "#24D249"],
                    [0.375, "#25D042"],
                    [0.4167, "#26CC58"],
                    [0.4583, "#28C86D"],
                    [0.50, "#29C481"],
                    [0.54167, "#2AC093"],
                    [0.5833, "#2BBCA4"],
                    [1.0, "#613099"],
                ],
                colorbar=dict(
                    title="Time of<br>Day",
                    x=0.93,
                    xpad=0,
                    nticks=24,
                    tickfont=dict(color="#d8d8d8"),
                    titlefont=dict(color="#d8d8d8"),
                    thicknessmode="pixels",
                ),
            ),
            mode="markers",
            # marker = {'color':'red'},
            # unselected = {'marker':{'opacity':1}},
            # selected = {'marker': {'opacity':0.5, 'size':25}},
            # hoverinfo = 'text' #,
            # hovertext = df_sub['hov_txt'],
        )
    ]

    if selectedLocation:
        zoom = 15.0
        latInitial = list_of_locations[selectedLocation]["lat"]
        lonInitial = list_of_locations[selectedLocation]["lon"]

    return {
        "data": locations,
        "layout": go.Layout(
            margin={"r":0,"t":0,"l":0,"b":0}, #get rid of default margins
            uirevision="foo",
            clickmode="event+select",
            hovermode="closest",
            hoverdistance=2,
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=25,
                style="dark",
                center=dict(lat=25.6823, lon=-100.3030),
                pitch=40,
                zoom=11.5,
            ),
        ),
    }


app.run_server(debug=True)
