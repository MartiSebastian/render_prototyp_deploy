# -*- coding: utf-8 -*-
from dash import Dash, dcc, Output, Input, State, html
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

# marker_svg = open(r"C:\Users\sebas\Documents\ladestationen_poi.svg").read()

# Vorbereiten der Daten
df = pd.read_csv("https://raw.githubusercontent.com/SebaMarti/render_prototyp_deploy/main/Daten_Ladestationen.csv")
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(x=df["X"], y=df["Y"], crs="EPSG:2056"))
gdf_WGS84 = gdf.to_crs(4326)

df_positionen =  pd.read_csv("https://raw.githubusercontent.com/SebaMarti/render_prototyp_deploy/main/Positionen.csv")
gdf_positionen = gpd.GeoDataFrame(df_positionen, geometry=gpd.points_from_xy(x=df_positionen["X"], y=df_positionen["Y"], crs="EPSG:2056"))
gdf_positionen_WGS84 = gdf_positionen.to_crs(4326)

Orte = list(gdf_positionen_WGS84["Orte"])

columns = gdf_WGS84.columns
col_distanz = []
gdf_WGS84["power"] = pd.to_numeric(gdf_WGS84["power"])
for i in columns[11:91]:
    gdf_WGS84[i] = pd.to_numeric(gdf_WGS84[i])
    if i.startswith("distanz"):
        col_distanz.append(i)


# Komponenten
app = Dash(__name__, external_stylesheets = [dbc.themes.FLATLY, 'https://codepen.io/chriddyp/pen/bWLwgP.css'])
server = app.server
mytitle = dcc.Markdown(children="")
mygraph = dcc.Graph(figure={}, config={"displayModeBar":False})

dropdown_start = dcc.Dropdown(id = "dropdown1",
                              options = Orte,
                              value = "Basel",
                              clearable = False
                              )

dropdown_end = dcc.Dropdown(id = "dropdown2", 
                            options = Orte,
                            clearable = True,
                            placeholder="Zielort wählen"
                            )

charging_mode = dcc.RadioItems(id = "radio_button",
                               value = "Laden in der Nähe",
                               inline = False
                               )

restreichweite = dcc.Slider(id = "slider1",
                            min = 0,
                            max = 400,
                            value = 100,
                            marks = {0:"0", 50:"50", 100:"100", 150:"150", 200:"200", 250:"250", 300:"300", 350:"350", 400:"400"},
                            tooltip = {"placement": "bottom","always_visible": False},
                            updatemode = "drag"
                            )

# Filter Ladeleistung
filter_ladeleistung = dcc.RangeSlider(id = "slider_filter_ladeleistung",
                                      min = 0, 
                                      max = 300,
                                      step = 1,
                                      value = [0,300],
                                      marks = {0:"0", 50:"50", 100:"100", 150:"150", 200:"200", 250:"250", 300:"300"},
                                      tooltip = {"placement": "bottom","always_visible": False},
                                      updatemode = "drag"
                                      )

button_filter_ladeleistung = dbc.CardHeader(
                              dbc.Button(
                                  "Filter Ladeleistung [kW]",
                                  id="button_ladeleistung",
                                  style={"margin-top":"5px", "text-transform":None}
                                  )
                              )

filter_ladeleistung_collapse = dbc.Collapse(
                                dbc.Card(dbc.CardBody(filter_ladeleistung)),
                                id="collapse_ladeleistung",
                                is_open=False)

# Filter Steckertyp
filter_steckertyp = dcc.Checklist(id = "checklist1",
                                  options = [{"label": " CCS", "value": "CCS"},
                                            {"label": " CHAdeMO", "value": "CHAdeMO"},
                                            {"label": " Haushaltssteckdose", "value": "Haushaltssteckdose"},
                                            {"label": " Haushaltssteckdose Schuko", "value": "Haushaltssteckdose Schuko"},
                                            {"label": " Kabel Typ 1", "value": "Kabel Typ 1"},
                                            {"label": " Kabel Typ 2", "value": "Kabel Typ 2"},
                                            {"label": " Steckdose Typ 2", "value": "Steckdose Typ 2"},
                                            {"label": " Tesla", "value": "Tesla"}],
                                  value = ["CCS", "CHAdeMO", "Haushaltssteckdose", "Haushaltssteckdose Schuko", "Kabel Typ 1", "Kabel Typ 2", "Steckdose Typ 2", "Tesla"])

button_filter_steckertyp = dbc.CardHeader(
                              dbc.Button(
                                  "Filter Steckertyp",
                                  id="button_steckertyp",
                                  style={"margin-top":"5px"}
                                  )
                              )

filter_steckertyp_collapse = dbc.Collapse(
                                dbc.Card(dbc.CardBody(filter_steckertyp)),
                                id="collapse_steckertyp",
                                is_open=False)

# Filter Ladenetzwerk
filter_ladenetzwerk = dcc.Checklist(id = "checklist2",
                                  options = [{"label": " eCarUp", "value": "eCarUp"},
                                             {"label": " en mobilecharge", "value": "en mobilecharge "},
                                             {"label": " evpass", "value": "evpass"},
                                             {"label": " EWAcharge", "value": "EWAcharge"},
                                             {"label": " IONITY", "value": "IONITY"},
                                             {"label": " Lidl Schweiz", "value": "Lidl Schweiz"},
                                             {"label": " Migrol Fast Charging", "value": "Migrol Fast Charging"},
                                             {"label": " mobilecharge", "value": "mobilecharge"},
                                             {"label": " Move", "value": "Move"},
                                             {"label": " PLUG'N ROLL", "value": "PLUG'N ROLL"},
                                             {"label": " Swisscharge", "value": "Swisscharge"},
                                             {"label": " Tesla", "value": "Tesla"},
                                             {"label": " Weitere", "value": "Weitere"}
                                            ],
                                  value = ["eCarUp", "en mobilecharge ", "evpass", "EWAcharge", "IONITY", "Lidl Schweiz", "Migrol Fast Charging", "mobilecharge", "Move", "PLUG'N ROLL", "Swisscharge", "Tesla", "Weitere"]
                                  )

button_filter_ladenetzwerk = dbc.CardHeader(
                              dbc.Button(
                                  "Filter Ladenetzwerk",
                                  id="button_ladenetzwerk",
                                  style={"margin-top":"5px"}
                                  )
                              )

filter_ladenetzwerk_collapse = dbc.Collapse(
                                dbc.Card(dbc.CardBody(filter_ladenetzwerk)),
                                id="collapse_ladenetzwerk",
                                is_open=False)



# Layout
app.layout = html.Div([
    html.Div(html.H4("Adaptive Visualisierung der Relevanz von öffentlichen Ladestationen (Prototyp)"), style={"text-align":"center", "margin-top":"20px"}),
    html.Hr(),
    html.Div([mytitle], style={"margin-left":"35.5%"}),
    html.Div([
        html.Div([
          mygraph
          ], style={'display': 'inline-block', 'vertical-align': 'top', "margin-left":"35.5%"}),
        html.Div([
          dropdown_start,
          dropdown_end,
          charging_mode,
          restreichweite,
          button_filter_ladeleistung,
          filter_ladeleistung_collapse,
          button_filter_steckertyp,
          filter_steckertyp_collapse,
          button_filter_ladenetzwerk,
          filter_ladenetzwerk_collapse
          ],
          style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '20px', 'width':'300px'})
        ]),
    ])



@app.callback(
    Output("collapse_ladeleistung", "is_open"),
    [Input("button_ladeleistung", "n_clicks")],
    [State("collapse_ladeleistung","is_open")],
    )

def collapse_ladeleistung(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse_steckertyp", "is_open"),
    [Input("button_steckertyp", "n_clicks")],
    [State("collapse_steckertyp","is_open")],
    )

def collapse_steckertyp(n, is_open):
    if n:
        return not is_open
    return is_open
        
@app.callback(
    Output("collapse_ladenetzwerk", "is_open"),
    [Input("button_ladenetzwerk", "n_clicks")],
    [State("collapse_ladenetzwerk","is_open")],
    )

def collapse_ladenetzwerk(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output(component_id="radio_button", component_property="options"),
    Output(component_id="radio_button", component_property="value"),
    Input(component_id="radio_button", component_property="value"),
    Input(component_id="dropdown1", component_property="value"),
    Input(component_id="dropdown2", component_property="value"),
    Input(component_id="slider1", component_property="value")
)
def update(radio_input, user_input_start, user_input_end, restreichweite):
    """
    If C is selected B should be disabled. If B is selected C should be disabled. A should always be enabled.
    """
    if user_input_end is None:
        return [
                {"label": " Laden in der Nähe", "value": "Laden in der Nähe"},
                {"label": html.Div(["En-Route-Charging"], style={"color":"Grey", "display":"inline-block","margin-left":"4px"}), "value": "En-Route-Charging", "disabled": True},
                {"label": html.Div(["Destination-Charging"], style={"color":"Grey", "display":"inline-block", "margin-left":"4px"}), "value": "Destination-Charging", "disabled": True}
              ], "Laden in der Nähe"
    elif user_input_end is not None:
        if restreichweite*1000 > float(gdf_positionen_WGS84[gdf_positionen_WGS84["Orte"] == user_input_start][user_input_end]):
            return [
                    {"label": " Laden in der Nähe", "value": "Laden in der Nähe"},
                    {"label": " En-Route-Charging", "value": "En-Route-Charging", "disabled": False},
                    {"label": " Destination-Charging", "value": "Destination-Charging", "disabled": False}
                  ], radio_input
        else:
            return [
                    {"label": " Laden in der Nähe", "value": "Laden in der Nähe"},
                    {"label": " En-Route-Charging", "value": "En-Route-Charging", "disabled": False},
                    {"label": html.Div(["Destination-Charging"], style={"color":"Grey", "display":"inline-block", "margin-left":"4px"}), "value": "Destination-Charging", "disabled": True}
                  ], radio_input
    

# Callback
@app.callback(
    Output(mygraph,"figure"),
    Output(mytitle, "children"),
    Input(component_id="dropdown1", component_property="value"),
    Input(component_id="dropdown2", component_property="value"),
    Input(component_id="radio_button", component_property="value"),
    Input(component_id="slider1", component_property="value"),
    Input(component_id="slider_filter_ladeleistung", component_property="value"),
    Input(component_id="checklist1", component_property="value"),
    Input(component_id="checklist2", component_property="value")
)

def update_graph(user_input_start, user_input_end, charging_mode, restreichweite, filter_ladeleistung, filter_steckertyp, filter_ladenetzwerk):
    col_name_distanz = col_distanz[Orte.index(user_input_start)]
    gdf_WGS84_erreichbar = gdf_WGS84[gdf_WGS84[col_name_distanz] <= restreichweite*1000]
    
    gdf_WGS84_filter = gdf_WGS84_erreichbar[(gdf_WGS84_erreichbar["power"] >= filter_ladeleistung[0]) & 
                                            (gdf_WGS84_erreichbar["power"] <= filter_ladeleistung[1]) & 
                                            (gdf_WGS84_erreichbar["Plugs"].isin(filter_steckertyp)) &
                                            (gdf_WGS84_erreichbar["Ladenetzwerke_Filter"].isin(filter_ladenetzwerk))
                                            ]
    x = gdf_WGS84_filter["geometry"].x
    y = gdf_WGS84_filter["geometry"].y
    
    fig = px.scatter_mapbox(gdf_WGS84_filter, lat=y, lon=x, color=gdf_WGS84_filter["power"], hover_data=[col_name_distanz], color_continuous_scale=px.colors.cyclical.IceFire, height = 585, width = 310)        
    fig.update(layout_coloraxis_showscale=False)
    
    # Position des Startorts berechnen und Punkt hinzufügen
    pos_start = gdf_positionen_WGS84[gdf_positionen_WGS84["Orte"] == user_input_start]
    x_pos_start = pos_start["geometry"].x
    y_pos_start = pos_start["geometry"].y
    fig.add_trace(go.Scattermapbox(lat=[float(y_pos_start)], lon=[float(x_pos_start)], mode="markers", marker=dict(size=15, color="blue")))
    title = user_input_start
    
    if user_input_end is not None: # Wenn Zielort definiert ist, dass Position des Zielorts berechnen und Punkt hinzufügen
        pos_end = gdf_positionen_WGS84[gdf_positionen_WGS84["Orte"] == user_input_end]    
        x_pos_end = pos_end["geometry"].x
        y_pos_end = pos_end["geometry"].y
        fig.add_trace(go.Scattermapbox(lat=[float(y_pos_end)], lon=[float(x_pos_end)], mode="markers", marker=dict(size=15, color="red", symbol="circle")))
        title = "von " + user_input_start + " nach " + user_input_end
    if charging_mode == "Laden in der Nähe":
        pos_x = x_pos_start
        pos_y = y_pos_start
        z = 12
    elif charging_mode == "En-Route-Charging":
        pos_x = (float(x_pos_start) + float(x_pos_end))/2
        pos_y = (float(y_pos_start) + float( y_pos_end))/2
        z = 7
    else:
        pos_x = x_pos_end
        pos_y = y_pos_end
        z = 12
      
    fig.update_layout(mapbox_style="open-street-map", showlegend=False, mapbox=dict(center=dict(lat=float(pos_y), lon=float(pos_x)), zoom=z, uirevision= "foo"))
    #                   mapbox_layers=[
    #                       {"below": 'traces',
    #                        "sourcetype": "raster",
    #                        "source": ["https://vectortiles.geo.admin.ch/tiles/ch.swisstopo.leichte-basiskarte.vt/v2.0.0/ch.swisstopo.leichte-basiskarte.vt.mbtiles"]
    #                       }])
    
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig, title

if __name__=='__main__':
    app.run_server(debug=True)
    
    
