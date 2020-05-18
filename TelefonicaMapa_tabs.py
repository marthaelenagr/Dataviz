# Dataset Telefónica
# María José Vota, Eugenia Rendón, Alan Velasco, Martha Elena García

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly as py
import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objs as go
from plotly.graph_objs import *
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
app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Analisis', value='tab-1'),
        dcc.Tab(label='Mapa', value='tab-2'),
        dcc.Tab(label='Voronoi', value='tab-3')
    ]),
    html.Div(id='tabs-content')
])

# Output en tabs
@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H3('Tab content 1: Analisis')
        ])
    elif tab == 'tab-2':
        return html.Div([
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
                            html.H2("Análisis de Tráfico de Datos"),
                            html.P(
                                """Seleccione el lunes de la semana que desea visualizar utilizando el calendario."""
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
                            dcc.Markdown(children=["TEC de MTY, 2020"]),
                        ],
                    ),
                    # Column for app graphs and plots
                    html.Div(
                        className="eight columns div-for-charts bg-grey",
                        children=[
                            dcc.Graph(id="map-graph", style={"backgroundColor": "#343332"}),
                            html.Div(
                                className="text-padding",
                                children=[
                                    "Seleccione cualquiera de las barras en el histograma "
                                    "para visualizar el consumo de datos en ese periodo de tiempo."
                                ],
                            ),
                            dcc.Graph(id="histogram"),
                        ],
                    ),
                ],
            )
        ])
    elif tab == 'tab-3':
        return html.Div([
            html.H3('Tab content 3: Voronoi')
        ])

#######

#Obtener cantidad de bytes por semana. 
# Pinta de otro color la barra seleccionada
def get_selection(week, pickedTech, pickedPlan):
    xVal = []
    yVal = []
    xSelected = []
    colorVal = [
        "#F4EC15",
        "#DAF017",
        "#BBEC19",
        "#9DE81B",
        "#80E41D",
        "#66E01F",
        "#4CDC20",
        "#34D822",
        "#24D249",
        "#25D042",
        "#26CC58",
        "#28C86D",
        "#29C481",
        "#2AC093",
        "#2BBCA4",
        "#2BB5B8",
        "#2C99B4",
        "#2D7EB0",
        "#2D65AC",
        "#2E4EA4",
        "#2E38A4",
        "#3B2FA0",
        "#4E2F9C",
        "#603099",
    ]

    # Put selected WEEKS into a list of numbers xSelected
    xSelected.extend([int(x) for x in week])

    #utilizando 10 semanas
    for i in range(10):
        # If bar is selected then color it white
        if i in xSelected and len(xSelected) < 10:
            colorVal[i] = "#FFFFFF"
        xVal.append(i)
        #CAMBIAR ESTO A SEMANAS
        # Get the number of rides at a particular time
        yVal.append(len(totalList[month][day][totalList[month][day].index.hour == i]))
    return [np.array(xVal), np.array(yVal), np.array(colorVal)]

#Output de histograma
# Update Histogram Figure based on Month, Day and Times Chosen
@app.callback(
    Output("histogram", "figure"),
    [
        Input("date-picker", "value"), 
        Input("tech_name", "value"), 
        Input("tipo_plan", "value")
    ],
)
def update_histogram(pickedWeek, pickedTech, pickedPlan):
    
    [xVal, yVal, colorVal] = get_selection(pickedWeek, pickedTech, pickedPlan)

    layout = go.Layout(
        bargap=0.01,
        bargroupgap=0,
        barmode="group",
        margin=go.layout.Margin(l=10, r=0, t=0, b=50),
        showlegend=False,
        plot_bgcolor="#323130",
        paper_bgcolor="#323130",
        dragmode="select",
        font=dict(color="white"),
        xaxis=dict(
            range=[-0.5, 23.5],
            showgrid=False,
            nticks=25,
            fixedrange=True,
            ticksuffix=":00",
        ),
        yaxis=dict(
            range=[0, max(yVal) + max(yVal) / 4],
            showticklabels=False,
            showgrid=False,
            fixedrange=True,
            rangemode="nonnegative",
            zeroline=False,
        ),
        annotations=[
            dict(
                x=xi,
                y=yi,
                text=str(yi),
                xanchor="center",
                yanchor="bottom",
                showarrow=False,
                font=dict(color="white"),
            )
            for xi, yi in zip(xVal, yVal)
        ],
    )

    return go.Figure(
        data=[
            go.Bar(x=xVal, y=yVal, marker=dict(color=colorVal), hoverinfo="x"),
            go.Scatter(
                opacity=0,
                x=xVal,
                y=yVal / 2,
                hoverinfo="none",
                mode="markers",
                marker=dict(color="rgb(66, 134, 244, 0)", symbol="square", size=40),
                visible=True,
            ),
        ],
        layout=layout,
    )

#######


# Output del mapa
@app.callback(
    Output("map-graph", "figure"),
    [
        Input("date-picker", "date"),
        Input("location-dropdown", "value"),
        Input("tech_name", "value"),
        Input("tipo_plan", "value"),
    ],
)
def update_graph(datePicked, selectedLocation, chosen_tech, chosen_plan):
    df_sub = df
    if datePicked is not None:
        df_sub = df_sub[df_sub["fecha"] == datePicked]
    if chosen_tech is not None:
        df_sub = df_sub[df_sub["tecnologia"] == chosen_tech]
    if chosen_plan is not None:
        df_sub = df_sub[df_sub["tipo_plan"] == chosen_plan]

    df_sub = (
        df_sub.groupby(["sitio", "longitud", "latitud"])
        .agg({"sum_bytes": "sum"})
        .reset_index()
    )

    if selectedLocation:
        zoom = 15.0
        latInitial = list_of_locations[selectedLocation]["lat"]
        lonInitial = list_of_locations[selectedLocation]["lon"]

    # Create figure
    return go.Figure(
        data=[
            Scattermapbox(
                lon=df_sub["longitud"],
                lat=df_sub["latitud"],
                #teras=df_sub["sum_bytes"]/1000000000000,
                marker=dict(
                    showscale=True,
                    color=df_sub['sum_bytes'],
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
                        title="Consumo<br>Datos",
                        x=0.93,
                        xpad=0,
                        nticks=24,
                        tickfont=dict(color="#d8d8d8"),
                        titlefont=dict(color="#d8d8d8"),
                        thicknessmode="pixels",
                    ),
                ),
                mode="markers+text",
                hovertemplate=(
                    # "<b>%{sitio} </b><br>"
                    "(%{lat},%{lon})<br>"
                    #"Consumo Datos: %{teras}<br>"
                    "<extra></extra>"
                ),
            ),
            # Plot important locations on the map
            Scattermapbox(
                lat=[list_of_locations[i]["lat"] for i in list_of_locations],
                lon=[list_of_locations[i]["lon"] for i in list_of_locations],
                mode="markers",
                hoverinfo="text",
                text=[i for i in list_of_locations],
                marker=dict(size=8, color="#ffa0a0"),
            ),
        ],
        layout=Layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},  # get rid of default margins
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
                zoom=10,
            ),
        ),
)


app.run_server(debug=True)