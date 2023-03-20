# -*- coding: utf-8 -*-
from dash import Dash, dcc, Output, Input, State, html
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import json
import urllib.request
import numpy as np

### Vorbereiten der Daten
# Daten zu Ladestationen laden
df = pd.read_csv("https://raw.githubusercontent.com/SebaMarti/render_prototyp_deploy/main/Daten_Ladestationen.csv")
#df = pd.read_csv("Daten_Ladestationen.csv")
gdf_WGS84 = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(x=df["X"], y=df["Y"], crs="EPSG:2056")).to_crs(4326)

# Attributnamen bestimmen
columns = gdf_WGS84.columns
col_distanz = []
gdf_WGS84["power"] = pd.to_numeric(gdf_WGS84["power"]) # Ladeleistung in numerische Werte umwandeln
gdf_WGS84.iloc[:, 11:108] = gdf_WGS84.iloc[:, 11:108].astype(float)
for i in columns[11:108]: # weitere Spalten in numerische Werte umwandeln
    gdf_WGS84[i] = pd.to_numeric(gdf_WGS84[i])
    if i.startswith("distanz"):
        col_distanz.append(i)


# Abrufen der Verfügbarkeit der Ladestationen
with urllib.request.urlopen(r"https://data.geo.admin.ch/ch.bfe.ladestellen-elektromobilitaet/status/oicp/ch.bfe.ladestellen-elektromobilitaet.json") as json_data:
    data = json.loads(json_data.read())

statuses = pd.concat([pd.json_normalize(d["EVSEStatusRecord"]) for d in data["EVSEStatuses"]], ignore_index=True) # Status (Verfügbarkeit) der Ladestationen in einem df zusammenfassen
statuses.columns.values[0] = "Location_ID"

# Daten zu Ladestationen und Verfügbarkeit zusammenführen
gdf_WGS84_merged = pd.merge(gdf_WGS84, statuses, how="left", on="Location_ID")
gdf_WGS84_merged["EVSEStatus"] = gdf_WGS84_merged["EVSEStatus"].replace(['Available', 'Occupied', 'Unknown'], ['Verfügbar', 'Besetzt', 'Unbekannt'])
gdf_WGS84_statuses = gdf_WGS84_merged[(gdf_WGS84_merged["EVSEStatus"].notnull()) & (gdf_WGS84_merged["EVSEStatus"] != "OutOfService")]


# Daten zu Start- und Zielorten laden
df_positionen =  pd.read_csv("https://raw.githubusercontent.com/SebaMarti/render_prototyp_deploy/main/Positionen.csv")
#df_positionen =  pd.read_csv("Positionen.csv")
gdf_positionen_WGS84 = gpd.GeoDataFrame(df_positionen, geometry=gpd.points_from_xy(x=df_positionen["X"], y=df_positionen["Y"], crs="EPSG:2056")).to_crs(4326)

# Ortsnamen bestimmen
Orte = list(gdf_positionen_WGS84["orte"])

# Mapbox token setzen
mapbox_token = ""
px.set_mapbox_access_token(mapbox_token)


##################################################################################
# Dash Komponenten definieren
app = Dash(__name__, external_stylesheets = [dbc.themes.FLATLY, 'https://codepen.io/chriddyp/pen/bWLwgP.css'])

# Titel
titel = dcc.Markdown(id = "id_titel", 
                     children="")

# Karte
karte = dcc.Graph(id="id_graph",
                  figure={},
                  config={"displayModeBar":False})

# Informationsfeld zu selektrierter Ladestation
informationen_ladestation = dbc.CardBody(id = "id_informationen_ladestation",
                                         children = "")

# Informationen zur Ladestation zu Card zusammenfassen
informationen_ladestation_card = dbc.Card(informationen_ladestation,
                                          style={"margin-top":"4px"})

# Dropdown Startort
startort_dropdown = dcc.Dropdown(id = "id_startort_dropdown",
                                 options = Orte,
                                 value = "Basel",
                                 clearable = False
                                 )

# Dropdown Zielort
zielort_dropdown = dcc.Dropdown(id = "id_zielort_dropdown", 
                                options = Orte,
                                placeholder="Zielort wählen..."
                                )

# Art des Ladens wählen (Radiobuttons)
charging_mode_radioitem = html.Div([dbc.RadioItems(id = "id_charging_mode",
                                                   className="btn-group",
                                                   inputClassName="btn-check",
                                                   labelClassName="btn btn-outline-primary",
                                                   labelCheckedClassName="active",
                                                   value = "Laden in der Nähe",
                                                   style={"margin-top":"5px"}
                                                   )],
                                    className="radio-group")

# Abonnement
abo_dropdown = dcc.Dropdown(id = "id_abo_dropdown",
                            options =["Swisscharge (kostenlos)", "MOVE light (kostenlos)", "evpass EXPLORER"],
                            value = "Swisscharge (kostenlos)",
                            clearable = False,
                            style={"margin-top":"0px"}
                            )


# Ladeprofil
ladeprofil_dropdown = dcc.Dropdown(id = "id_ladeprofil_dropdown",
                                   options =[{"label":"Standard", "value":"Standard"},
                                             {"label":"Tiefe Kosten", "value":"Tiefe Kosten"},
                                             {"label":"Hohe Ladeleistung","value":"Hohe Ladeleistung"},
                                             {"label":html.Span(["Neues Ladeprofil erstellen..."], style={"font-style":"italic"}), "value":"Neues Ladeprofil erstellen..."}
                                            ],
                                   value = "Standard",
                                   clearable = False,
                                   style={"margin-top":"0px"}
                                   )

### Filter
# Filter Verfügbarkeit
filter_verfuegbarkeit_checklist = dcc.Checklist(id = "id_verfuegbarkeit_checklist",
                                                options = [{"label": " Nur verfügbare Ladestationen anzeigen", "value": "Nur verfügbare Ladestationen anzeigen"}],
                                                value = ["Nur verfügbare Ladestationen anzeigen"]
                                                )

# Filter Ladeleistung
filter_ladeleistung_rangeslider = dcc.RangeSlider(id = "id_ladeleistung_rangeslider",
                                                  min = 0, 
                                                  max = 300,
                                                  step = 1,
                                                  value = [0,300],
                                                  marks = {0:"0", 50:"50", 100:"100", 150:"150", 200:"200", 250:"250", 300:"300"},
                                                  tooltip = {"placement": "bottom","always_visible": False},
                                                  updatemode = "mouseup"
                                                  )

filter_ladeleistung_button = dbc.CardHeader(dbc.Button("Ladeleistung [kW] ⮟",
                                                       id="id_ladeleistung_button",
                                                       style={"margin-left":"0px", "font-size":"12px"}
                                                       ),
                                            style={"background-color":"white", "border":"0px", "padding":"0px"}
                                            )

filter_ladeleistung_collapse = dbc.Collapse(dbc.Card(dbc.CardBody(filter_ladeleistung_rangeslider)),
                                            id="id_ladeleistung_collapse",
                                            is_open=False)

# Filter Steckertyp
filter_steckertyp_checklist = dcc.Checklist(id = "id_steckertyp_checklist",
                                            options = [{"label": " CCS", "value": "CCS"},
                                                       {"label": " CHAdeMO", "value": "CHAdeMO"},
                                                       {"label": " Haushaltssteckdose", "value": "Haushaltssteckdose"},
                                                       {"label": " Haushaltssteckdose Schuko", "value": "Haushaltssteckdose Schuko"},
                                                       {"label": " Kabel Typ 1", "value": "Kabel Typ 1"},
                                                       {"label": " Kabel Typ 2", "value": "Kabel Typ 2"},
                                                       {"label": " Steckdose Typ 2", "value": "Steckdose Typ 2"},
                                                       {"label": " Tesla", "value": "Tesla"}])

filter_steckertyp_button = dbc.CardHeader(dbc.Button("Steckertyp ⮟",
                                                     id="id_steckertyp_button",
                                                     style={"margin-left":"0px", "font-size":"12px"}
                                                     ),
                                          style={"background-color":"white", "border":"0px", "padding":"0px", "margin-top":"4px"}
                                          )

filter_steckertyp_collapse = dbc.Collapse(dbc.Card(dbc.CardBody(filter_steckertyp_checklist)),
                                          id="id_steckertyp_collapse",
                                          is_open=False)

# Filter Ladenetzwerk
filter_ladenetzwerk_checklist = dcc.Checklist(id = "id_ladenetzwerk_checklist",
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

filter_ladenetzwerk_button = dbc.CardHeader(dbc.Button("Ladenetzwerk ⮟",
                                                       id="id_ladenetzwerk_button",
                                                       style={"margin-left":"0px", "font-size":"12px"}
                                                       ),
                                            style={"background-color":"white", "border":"0px", "padding":"0px", "margin-top":"4px"}
                                            )

filter_ladenetzwerk_collapse = dbc.Collapse(dbc.Card(dbc.CardBody(filter_ladenetzwerk_checklist)),
                                            id="id_ladenetzwerk_collapse",
                                            is_open=False)

# Filter Distanz
filter_distanz_slider = dcc.Slider(id = "id_distanz_slider",
                                   min = 0, 
                                   max = 20,
                                   step = 1,
                                   marks = {0:"0", 5:"5", 10:"10", 15:"15", 20:"20"},
                                   tooltip = {"placement": "bottom","always_visible": False},
                                   updatemode = "mouseup"
                                   )

filter_distanz_button = dbc.CardHeader(dbc.Button("Distanz/Umweg [km]⮟",
                                                  id="id_distanz_button",
                                                  style={"margin-left":"0px", "font-size":"12px"}
                                                  ),
                                       style={"background-color":"white", "border":"0px", "padding":"0px", "margin-top":"4px"}
                                       )

filter_distanz_collapse = dbc.Collapse(dbc.Card(dbc.CardBody(filter_distanz_slider)),
                                       id="id_distanz_collapse",
                                       is_open=False)

# Filter zu Card zusammenfassen
filteroptionen_card = dbc.Card(dbc.CardBody([html.P("Filter", style={"font-weight":"bold", "margin-bottom":"2px", "margin-top":"0px"}),
                                             filter_verfuegbarkeit_checklist,
                                             filter_ladeleistung_button,
                                             filter_ladeleistung_collapse,
                                             filter_steckertyp_button,
                                             filter_steckertyp_collapse,
                                             filter_ladenetzwerk_button,
                                             filter_ladenetzwerk_collapse,
                                             filter_distanz_button,
                                             filter_distanz_collapse]),
                               style={"margin-top":"4px"})


### Fahrzeuginformationen
# Fahrzeugtyp
fahrzeugtyp_dropdown = dcc.Dropdown(id = "id_fahrzeugtyp_dropdown",
                                    options =["Škoda Enyaq iV 60 (2022)", "Porsche Taycan", "Nissan Leaf e+ 62kWh (2019)"] ,
                                    value = "Škoda Enyaq iV 60 (2022)",
                                    clearable = False
                                    )

# Restreichweite
restreichweite_slider = dcc.Slider(id = "id_restreichweite_slider",
                                   min = 0,
                                   max = 350,
                                   value = 100,
                                   marks = {0:"0", 50:"50", 100:"100", 150:"150", 200:"200", 250:"250", 300:"300", 350:"350"},
                                   tooltip = {"placement": "bottom","always_visible": False},
                                   updatemode = "mouseup"
                                   )
                 
# Fahrzeuginformationen zu Card zusammenfassen
fahrzeuginformationen_card = dbc.Card(dbc.CardBody([html.P("Fahrzeuginformationen",style={"font-weight":"bold", "margin-bottom":"2px", "margin-top":"0px"}),
                                                    html.P("Fahrzeugmodell:", style={"margin-bottom":"0px"}),
                                                    fahrzeugtyp_dropdown,
                                                    html.P("Restreichweite [km]:", style={"margin-top":"5px", "margin-bottom":"0px"}),
                                                    restreichweite_slider]),
                                      style={"margin-top":"5px"})
                        
 
### Gewichtung des Ladeprofils          
# Gewichtung Kosten
gewichtung_kosten = dcc.Slider(id = "id_gewichtung_kosten",
                               min = 0,
                               max = 5,
                               step = 0.1,
                               marks = {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5"},
                               tooltip = {"placement": "bottom","always_visible": False},
                               updatemode = "mouseup"
                               )

# Gewichtung Ladeleistung
gewichtung_ladeleistung = dcc.Slider(id = "id_gewichtung_ladeleistung",
                                     min = 0,
                                     max = 5,
                                     step = 0.1,
                                     marks = {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5"},
                                     tooltip = {"placement": "bottom","always_visible": False},
                                     updatemode = "mouseup"
                                     )

# Gewichtung Distanz
gewichtung_distanz = dcc.Slider(id = "id_gewichtung_distanz",
                                min = 0,
                                max = 5,
                                step = 0.1,
                                marks = {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5"},
                                tooltip = {"placement": "bottom","always_visible": False},
                                updatemode = "mouseup"
                                )

# Gewichtung Fahrdauer
gewichtung_fahrdauer = dcc.Slider(id = "id_gewichtung_fahrdauer",
                                  min = 0,
                                  max = 5,
                                  step = 0.1,
                                  marks = {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5"},
                                  tooltip = {"placement": "bottom","always_visible": False},
                                  updatemode = "mouseup"
                                  )

# Gewichtung zu Card zusammenfügen
gewichtungsoptionen_card = dbc.Card(dbc.CardBody([html.P("Gewichtung (Ladeprofil)", style={"font-weight":"bold", "margin-bottom":"2px", "margin-top":"0px"}),
                                                  html.P("Kosten:", style={"margin-bottom":"0px"}),
                                                  gewichtung_kosten,
                                                  html.P("Ladeleistung [kW]:", style={"margin-top":"5px", "margin-bottom":"0px"}),
                                                  gewichtung_ladeleistung,
                                                  html.P("Distanz:", style={"margin-top":"5px", "margin-bottom":"0px"}),
                                                  gewichtung_distanz,
                                                  html.P("Fahrdauer:", style={"margin-top":"5px", "margin-bottom":"0px"}),
                                                  gewichtung_fahrdauer]),
                                    style={"margin-top":"5px"})


####################################################################################
# Layout
app.layout = html.Div([dcc.Store(id='id_store_fahrzeugeigenschaften', storage_type='session'),
                       # dcc.Store(id='verfuegbarkeit', storage_type='memory'),
                       dcc.Store(id='id_gdf_filter', storage_type='memory'),
                       dcc.Store(id='id_col_names', storage_type='session'),
                       dcc.Store(id='id_relevance_score', storage_type='session'),
                       html.Div(html.H4("Adaptive Visualisierung der Relevanz von öffentlichen Ladestationen (Prototyp)"), style={"text-align":"center", "margin-top":"20px"}),
                       html.Hr(),
                       html.Div([titel], style={"margin-left":"35.5%"}),
                       html.Div([
                                 html.Div([karte, html.Div([informationen_ladestation_card])], style={'display': 'inline-block', 'vertical-align': 'top', "margin-left":"35.5%"}),
                                 html.Div([html.Div([html.Div([html.P("Startort:", style={"margin-bottom":"0px", "margin-top":"0px"}), html.Div(startort_dropdown)], style={'display': 'inline-block', 'width': '148px'}),
                                                     html.Div([html.P("Zielort:", style={"margin-bottom":"0px", "margin-top":"0px"}), html.Div(zielort_dropdown)], style={'display': 'inline-block', 'width': '148px', 'margin-left':"4px"})
                                                     ]),
                                           charging_mode_radioitem,
                                           html.Div([html.P("Abonnement:", style={"margin-bottom":"0px", "margin-top":"0px"}), html.Div(abo_dropdown)]),
                                           html.Div([html.P("Ladeprofil:", style={"margin-bottom":"0px", "margin-top":"0px"}), html.Div(ladeprofil_dropdown)]),
                                           filteroptionen_card,
                                           fahrzeuginformationen_card          
                                           ],
                                          style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '20px', 'width':'300px'}),
                                 html.Div([gewichtungsoptionen_card], style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '20px', 'width':'300px'})
                                 ])
                       ])

#####################################################################################
# Callbacks
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("id_ladeleistung_collapse", "is_open"),
    [Input("id_ladeleistung_button", "n_clicks")],
    [State("id_ladeleistung_collapse", "is_open")],
)
def toggle_ladeleistung(n, is_open):
    return toggle_collapse(n, is_open)

@app.callback(
    Output("id_ladeleistung_button", "children"),
    [Input("id_ladeleistung_button", "n_clicks")],
)
def text_button_ladeleistung(n):
    if n == None or (n % 2) == 0:
        return "Ladeleistung [kW] ⏷"
    else:
        return "Ladeleistung [kW] ⏶"

@app.callback(
    Output("id_steckertyp_collapse", "is_open"),
    [Input("id_steckertyp_button", "n_clicks")],
    [State("id_steckertyp_collapse", "is_open")],
)
def toggle_steckertyp(n, is_open):
    return toggle_collapse(n, is_open)

@app.callback(
    Output("id_steckertyp_button", "children"),
    [Input("id_steckertyp_button", "n_clicks")],
)
def text_button_steckertyp(n):
    if n == None or (n % 2) == 0:
        return "Steckertyp ⏷"
    else:
        return "Steckertyp ⏶"

@app.callback(
    Output("id_ladenetzwerk_collapse", "is_open"),
    [Input("id_ladenetzwerk_button", "n_clicks")],
    [State("id_ladenetzwerk_collapse","is_open")],
    )
def toggle_ladenetzwerk(n, is_open):
    return toggle_collapse(n, is_open)

@app.callback(
    Output("id_ladenetzwerk_button", "children"),
    [Input("id_ladenetzwerk_button", "n_clicks")],
    )
def text_button_ladeleistung(n):
    if n == None or (n % 2) == 0:
        return "Ladenetzwerk ⏷"
    else:
        return "Ladenetzwerk ⏶"

@app.callback(
    Output("id_distanz_collapse", "is_open"),
    [Input("id_distanz_button", "n_clicks")],
    [State("id_distanz_collapse","is_open")],
    )
def toggle_distanz(n, is_open):
    return toggle_collapse(n, is_open)

@app.callback(
    Output("id_distanz_button", "children"),
    [Input("id_distanz_button", "n_clicks")],
    )
def text_button_distanz(n):
    if n == None or (n % 2) == 0:
        return "Distanz/Umweg [km] ⏷"
    else:
        return "Distanz/Umweg [km] ⏶"


# Die Ladearten, die ausgewählt werden können hängt von der Restreichweite des Elektrofahrzeugs und dem gewählten Start- und Zielort ab. En-Route-Charging und Destination Charging sind nur verfügbar, wenn ein Zielort gewählt wurde
@app.callback(
    Output(component_id="id_charging_mode", component_property="options"),
    Output(component_id="id_charging_mode", component_property="value"),
    Input(component_id="id_charging_mode", component_property="value"),
    Input(component_id="id_startort_dropdown", component_property="value"),
    Input(component_id="id_zielort_dropdown", component_property="value"),
    Input(component_id="id_restreichweite_slider", component_property="value")
)

def update(charging_mode, startort, zielort, restreichweite):
    if zielort is None:
        return [
                {"label": " Laden in der Nähe", "value": "Laden in der Nähe"},
                {"label": "En-Route-Charging", "value": "En-Route-Charging", "disabled":True},
                {"label": "Destination-Charging", "value": "Destination-Charging", "disabled":True}
              ], "Laden in der Nähe"
    else:
        if restreichweite*1000 > float(gdf_positionen_WGS84[gdf_positionen_WGS84["orte"] == startort][zielort]):
            return [
                    {"label": " Laden in der Nähe", "value": "Laden in der Nähe"},
                    {"label": " En-Route-Charging", "value": "En-Route-Charging"},
                    {"label": " Destination-Charging", "value": "Destination-Charging"}
                  ], charging_mode
        else:
            return [
                    {"label": " Laden in der Nähe", "value": "Laden in der Nähe"},
                    {"label": " En-Route-Charging", "value": "En-Route-Charging"},
                    {"label": "Destination-Charging", "value": "Destination-Charging", "disabled":True}
                  ], charging_mode


# Gewichtungsanzeige
@app.callback(
    Output(component_id="id_gewichtung_kosten", component_property="value"),
    Output(component_id="id_gewichtung_ladeleistung", component_property="value"),
    Output(component_id="id_gewichtung_distanz", component_property="value"),
    Output(component_id="id_gewichtung_fahrdauer", component_property="value"),
    Output(component_id="id_gewichtung_kosten", component_property="disabled"),
    Output(component_id="id_gewichtung_ladeleistung", component_property="disabled"),
    Output(component_id="id_gewichtung_distanz", component_property="disabled"),
    Output(component_id="id_gewichtung_fahrdauer", component_property="disabled"),
    Output(component_id="id_distanz_slider", component_property="value"),
    Input(component_id="id_ladeprofil_dropdown", component_property="value"),
    Input(component_id="id_startort_dropdown", component_property="value"),
    Input(component_id="id_zielort_dropdown", component_property="value"),
    Input(component_id="id_charging_mode", component_property="value"),
)
def gewichtungsanzeige(ladeprofil, startort, zielort, charging_mode):
    if ladeprofil == "Standard":
        stadt = ["Basel", "Bern", "Lugano", "Zuerich"]
        land = ["Meiringen", "Zernez"]
        autobahn = ["Nyon", "Rothrist_Ost", "Rothrist_West"]
        if charging_mode == "Laden in der Nähe":
            if startort in stadt:
                return 2,1.5,1.5,1,True,True,True,True,3
            elif startort in land:
                return 1.5,2,1.5,1,True,True,True,True,10
            else:
                return 1.5,3,1.5,1,True,True,True,True,10
        elif charging_mode == "Destination-Charging":
            if zielort in stadt:
                return 2,1.5,1.5,1,True,True,True,True,3
            elif zielort in land:
                return 1.5,2,1.5,1,True,True,True,True,10
            else:
                return 1.5,3,1.5,1,True,True,True,True,10
        elif charging_mode == "En-Route-Charging":
            return 1.5,3,1.5,1,True,True,True,True,3
    elif ladeprofil == "Tiefe Kosten":
        return 4,1.5,1.5,1,True,True,True,True
    elif ladeprofil == "Hohe Ladeleistung":
        return 2,4,1.5,1,True,True,True,True
    elif ladeprofil == "Neues Ladeprofil erstellen...":
        return 1,1,1,1,False,False,False,False


# Fahrzeugeigenschaften bestimmen
@app.callback(
    Output(component_id="id_steckertyp_checklist", component_property="value"),
    Output(component_id="id_store_fahrzeugeigenschaften", component_property="data"),
    Input(component_id="id_fahrzeugtyp_dropdown", component_property="value")
)
def eigenschaften_fahrzeug(fahrzeugtyp):
    # Vom Fahrzeugtyp abhängige Eigenschaften bestimmen
    if fahrzeugtyp == "Škoda Enyaq iV 60 (2022)": # vgl. https://www.skoda-storyboard.com/de/pressemitteilungen-archive/skoda-enyaq-iv-familie-mit-noch-mehr-reichweite-und-komfort-dank-neuer-software/
        batteriekapazitaet = 58.0 # Nettokapazität
        max_ladeleistung_dc = 124.0
        max_ladeleistung_ac = 11.0
        phasen = 3
        plugs = ["Kabel Typ 2", "Steckdose Typ 2", "CCS"]
    elif fahrzeugtyp == "Porsche Taycan":
        batteriekapazitaet = 71.0 # Nettokapazität
        max_ladeleistung_dc = 223.0
        max_ladeleistung_ac = 22.0
        phasen = 3
        plugs = ["Kabel Typ 2", "Steckdose Typ 2", "CCS"]
    elif fahrzeugtyp == "Nissan Leaf e+ 62kWh (2019)": # vgl. https://de.nissan.ch/content/dam/Nissan/ch/de/brochures/pkw/leaf-2018-broschuere-preisliste.pdf, https://ev-database.org/car/1144/Nissan-Leaf-eplus#charge-table
        batteriekapazitaet = 59.0 # Nettokapazität
        max_ladeleistung_dc = 50.0
        max_ladeleistung_ac = 6.6 # lädt nur 1-phasig mit maximal 29 Ampere
        phasen = 1
        plugs = ["Kabel Typ 2", "Steckdose Typ 2", "CHAdeMO"]
      
    possible_values = ["CCS", "CHAdeMO", "Haushaltssteckdose", "Haushaltssteckdose Schuko", "Kabel Typ 1", "Kabel Typ 2", "Steckdose Typ 2", "Tesla"]
    steckertypen_value = [p for p in possible_values if p in plugs]
    return steckertypen_value, {"value": [batteriekapazitaet, max_ladeleistung_dc, max_ladeleistung_ac, phasen]}


# Daten filtern
@app.callback(
    Output(component_id="id_gdf_filter", component_property="data"),
    Output(component_id="id_col_names", component_property="data"),
    Input(component_id="id_startort_dropdown", component_property="value"),
    Input(component_id="id_zielort_dropdown", component_property="value"),
    Input(component_id="id_charging_mode", component_property="value"),
    Input(component_id="id_restreichweite_slider", component_property="value"),
    Input(component_id="id_ladeleistung_rangeslider", component_property="value"),
    Input(component_id="id_steckertyp_checklist", component_property="value"),
    Input(component_id="id_ladenetzwerk_checklist", component_property="value"),
    Input(component_id="id_verfuegbarkeit_checklist", component_property="value"),
    Input(component_id="id_distanz_slider", component_property="value"),
    Input(component_id="id_abo_dropdown", component_property="value"),
    Input(component_id="id_store_fahrzeugeigenschaften", component_property="data")
)
def filter_data(startort, zielort, charging_mode, restreichweite, filter_ladeleistung, filter_steckertyp, filter_ladenetzwerk, filter_verfuegbarkeit, filter_distanz, abonnement, fahrzeugeigenschaften):
    # Erreichbare Ladestationen herausfiltern
    col_name_distanz = col_distanz[Orte.index(startort)]
    restreichweite_m = restreichweite*1000
    distanz_filter = filter_distanz*1000
    if charging_mode == "Laden in der Nähe":
        erreichbar = (gdf_WGS84_statuses[col_name_distanz] <= restreichweite_m) & (gdf_WGS84_statuses[col_name_distanz] <= distanz_filter)
    elif charging_mode == "Destination-Charging":
        col_name_distanz_ziel = col_distanz[Orte.index(zielort)]
        erreichbar = (gdf_WGS84_statuses[col_name_distanz] <= restreichweite_m) & (gdf_WGS84_statuses[col_name_distanz_ziel] <= distanz_filter)
    elif charging_mode == "En-Route-Charging": # Falls möglich soll beim En-Route-Charging die verwendete Ladestation nahe genug am Zielort liegen, um die Strecke mit einem Ladestopp abzuschliessen
        col_name_distanz_ziel = col_distanz[Orte.index(zielort)]
        erreichbar_start = gdf_WGS84_statuses[col_name_distanz] <= restreichweite_m
        erreichbar_ziel = gdf_WGS84_statuses[col_name_distanz_ziel] <= 350000 # Distanz der Ladestation zum Zielort muss kleiner sein als die maximalen Reichweite (350'000 m).
        
        # Zudem soll die Ladestation innerhalb der im Filter angegebenen Distanz zur Fahrstrecke liegen
        col_dist_erc = [c for c in columns if startort.lower() in c and zielort.lower() in c and c.endswith("_distanz")][0] # Totale Distanz
        distanz_start_ziel_direkt = float(gdf_positionen_WGS84[gdf_positionen_WGS84["orte"] == startort][zielort])
        erreichbar_distanz = (gdf_WGS84_statuses[col_dist_erc] - distanz_start_ziel_direkt) <= distanz_filter
        erreichbar = erreichbar_start & erreichbar_ziel & erreichbar_distanz
    
    gdf_WGS84_erreichbar = gdf_WGS84_statuses[erreichbar]
    
    # Ladestationen nach weiteren Kriterien filtern (Status, Steckertyp, Ladenetzwerk, Ladeleistung)
    conditions = (gdf_WGS84_erreichbar["Plugs"].str.contains("|".join(filter_steckertyp))) & \
                 (gdf_WGS84_erreichbar["Ladenetzwerke_Filter"].str.contains("|".join(filter_ladenetzwerk)))
    
    if len(filter_ladenetzwerk) == 0 or len(filter_steckertyp) == 0:
        gdf_WGS84_filter = gdf_WGS84_erreichbar.iloc[:0]
    elif len(filter_verfuegbarkeit)>0 and filter_verfuegbarkeit[0] == "Nur verfügbare Ladestationen anzeigen":
        gdf_WGS84_filter = gdf_WGS84_erreichbar[(gdf_WGS84_erreichbar["EVSEStatus"] == "Verfügbar") & \
                                                (gdf_WGS84_erreichbar["power"] >= filter_ladeleistung[0]) & \
                                                (gdf_WGS84_erreichbar["power"] <= filter_ladeleistung[1]) & \
                                                conditions]
    else:
        gdf_WGS84_filter = gdf_WGS84_erreichbar[(gdf_WGS84_erreichbar["power"] >= filter_ladeleistung[0]) & \
                                                (gdf_WGS84_erreichbar["power"] <= filter_ladeleistung[1]) & \
                                                conditions]
    
    # Effektive Ladeleistung bestimmen
    batteriekapazitaet, max_ladeleistung_dc, max_ladeleistung_ac, phasen = fahrzeugeigenschaften["value"] # Fahrzeugeigenschaften
    def ladeleistung_effektiv(row, max_ladeleistung_dc, max_ladeleistung_ac, phasen):
        powertype = row["powertype"]
        power = row["power"]
    
        # Bedingungen aufstellen
        conditions = np.array([
            powertype == "DC",
            (powertype == "AC_3_PHASE") & (phasen == 3),
            (powertype == "AC_3_PHASE") & (phasen == 1),
            powertype == "AC_1_PHASE"
        ])
        
        results = np.array([
            np.minimum(power, max_ladeleistung_dc),
            np.minimum(power, max_ladeleistung_ac),
            np.minimum(power/3, max_ladeleistung_ac),
            np.minimum(power, max_ladeleistung_ac)
        ])
    
        return round(np.where(conditions, results, 0).max(),2)
    
    gdf_WGS84_filter["ladeleistung_eff"] = gdf_WGS84_filter.apply(ladeleistung_effektiv, args=(max_ladeleistung_dc, max_ladeleistung_ac, phasen), axis=1)


    # Kosten bestimmen um Elektrofahrzeug auf 100% der Batteriekapazität zu laden (als Vereinfachung wird jeweils die Restreichweite in die Batteriekapazität umgerechnet, wobei für alle Fahrzeugmodelle eine maximale Reichweite von 350km verwendet wird. In der Praxis wird das Elektrofahrzeug jedoch wenn möglich nur bis 80% geladen, da dies Batterieschonender ist. Auch nimmt die Ladeleistung mit zuhehmendem Ladezustand der Batterie stark ab)
    def kostenberechnung(row, abonnement, restreichweite, col_name_distanz, charging_mode, batteriekapazitaet):
        abo_optionen = {
            "Swisscharge (kostenlos)": [row["kosten_swi_kW"], row["kosten_swi_min"], row["kosten_swi_sta"]],
            "MOVE light (kostenlos)": [row["kosten_movli_kW"], row["kosten_movli_min"], row["kosten_movli_sta"]],
            "evpass EXPLORER": [row["kosten_evpex_kW"], row["kosten_evpex_min"], 0]
            }
        kosten_kw, kosten_min, kosten_start = abo_optionen.get(abonnement, [0, 0, 0])
        if charging_mode == "En-Route-Charging": # Beim Laden unterwegs werdend die Kosten für das Laden von 100km Reichweite berechnet (Annahme Verbrauch von 15kWh/100km).
            kWh = 15                             # Würde wie oben der Batterieladezustand beim Erreichen der Ladestation verwendet werden, wären weiter entfernte Ladestationen systematisch teuerer und somit weniger relevant. Beim En-Route-Charging spielt es aber keine Rolle, wo auf der Strecke zum Zielort geladen wird.    
        elif charging_mode == "Laden in der Nähe" or charging_mode == "Destination-Charging":
            kWh = ((350 - (restreichweite - (row[col_name_distanz]/1000)))/350) * batteriekapazitaet
        ladeleistung_eff = row["ladeleistung_eff"]
        kosten = round((kWh * kosten_kw) + (kWh/ladeleistung_eff*60) * kosten_min + kosten_start,2)
        return kosten

    gdf_WGS84_filter["Kosten"] = gdf_WGS84_filter.apply(kostenberechnung, args=(abonnement, restreichweite, col_name_distanz, charging_mode, batteriekapazitaet), axis=1)


    # Ladedauer bestimmen
    def ladedauer(row, charging_mode, restreichweite, col_name_distanz, batteriekapazitaet):
        ladeleistung_eff = row["ladeleistung_eff"]
        if charging_mode == "En-Route-Charging": # Beim Laden unterwegs werdend die Kosten für das Laden von 100km Reichweite berechnet (Annahme Verbrauch von 15kWh/100km).
            kWh = 15                             # Würde wie oben der Batterieladezustand beim Erreichen der Ladestation verwendet werden, wären weiter entfernte Ladestationen systematisch teuerer und somit weniger relevant. Beim En-Route-Charging spielt es aber keine Rolle, wo auf der Strecke zum Zielort geladen wird.    
        elif charging_mode == "Laden in der Nähe" or charging_mode == "Destination-Charging":
            kWh = ((350 - (restreichweite - (row[col_name_distanz]/1000)))/350) * batteriekapazitaet
        ladedauer_min = round((kWh/ladeleistung_eff)*60,0)
        return ladedauer_min
        
    gdf_WGS84_filter["ladedauer"] = gdf_WGS84_filter.apply(ladedauer, args=(charging_mode, restreichweite, col_name_distanz, batteriekapazitaet), axis=1)


    # Spaltennamen zuweisen (Distanz und Fahrdauer)
    if charging_mode == "Laden in der Nähe":
        col_dist = col_name_distanz
        col_fahrdauer = [c for c in columns if startort.lower() in c and "fahrdauer" in c][0]
    elif charging_mode == "En-Route-Charging":
        col_dist = [c for c in columns if startort.lower() in c and zielort.lower() in c and c.endswith("_distanz")][0]
        col_fahrdauer = [c for c in columns if startort.lower() in c and zielort.lower() in c and "_fahrdauer" in c][0]
    elif charging_mode == "Destination-Charging":
        col_dist = col_name_distanz_ziel
        col_fahrdauer = [c for c in columns if zielort.lower() in c and "fahrdauer" in c][0]
       
    colnames = {"col_dist":col_dist, "col_fahrdauer":col_fahrdauer}
    
    gdf_WGS84_filter["lon"] = gdf_WGS84_filter["geometry"].x
    gdf_WGS84_filter["lat"] = gdf_WGS84_filter["geometry"].y
    gdf_WGS84_filter = gdf_WGS84_filter.drop(columns="geometry") # Geometry kann nicht gespeichert werden! (Dash/Plotly Bug?)
    df_WGS84_dict = pd.DataFrame(gdf_WGS84_filter).to_dict("records")

    return df_WGS84_dict, colnames


# Relevanzwert berechnen und Karte erstellen
@app.callback(
    Output(component_id="id_graph",component_property="figure"),
    Output(component_id="id_relevance_score", component_property="data"),
    Output(component_id="id_titel", component_property="children"),
    Input(component_id="id_gdf_filter", component_property="data"),
    Input(component_id="id_col_names", component_property="data"),
    Input(component_id="id_startort_dropdown", component_property="value"),
    Input(component_id="id_zielort_dropdown", component_property="value"),
    Input(component_id="id_charging_mode", component_property="value"),
    Input(component_id="id_gewichtung_kosten", component_property="value"),
    Input(component_id="id_gewichtung_ladeleistung", component_property="value"),
    Input(component_id="id_gewichtung_distanz", component_property="value"),
    Input(component_id="id_gewichtung_fahrdauer", component_property="value"),
    Input(component_id="id_verfuegbarkeit_checklist", component_property="value")
)
def update_graph(gdf_WGS84_dict, col_names, startort, zielort, charging_mode, gewichtung_kosten, gewichtung_ladeleistung, gewichtung_distanz, gewichtung_fahrdauer, filter_verfuegbarkeit):
    # Kopie des DF erstellen
    df_WGS84_filter = pd.DataFrame.from_dict(gdf_WGS84_dict)
    gdf_WGS84_filter = gpd.GeoDataFrame(df_WGS84_filter)
    gdf_WGS84_copy = gdf_WGS84_filter.copy()
      
    # Wenn mindestens 1 Ladestation für die gewählten Filtereinstellungen vorhanden ist
    if len(gdf_WGS84_copy.index) != 0:
        
        ### Normalisierung der Werte
        # Kosten
        def kosten_norm(row):
            kosten_max = max(gdf_WGS84_copy["Kosten"])
            if kosten_max != 0:
                kosten_norm = 1-(row["Kosten"]/kosten_max)
            else:
                kosten_norm = 1
            return kosten_norm
        
        # Ladeleistung
        def ladeleistung_norm(row):
            ladeleistung_max = max(gdf_WGS84_copy["ladeleistung_eff"])
            ladeleistung_norm = row["ladeleistung_eff"]/ladeleistung_max
            return ladeleistung_norm
        
        # Distanz
        def distanz_norm(row):
            col_dist = col_names["col_dist"]
            distanz_max = max(gdf_WGS84_copy[col_dist])
            distanz_norm = 1-(row[col_dist]/distanz_max)
            return distanz_norm
                       
        # Fahrdauer
        def fahrdauer_norm(row):
            col_fahrdauer = col_names["col_fahrdauer"]
            fahrdauer_max = max(gdf_WGS84_copy[col_fahrdauer])
            fahrdauer_norm = 1-(row[col_fahrdauer]/fahrdauer_max)
            return fahrdauer_norm
        
        # def distanz_norm(column):
        #     max_value = column.max()
        #     data_norm = [x / max_value for x in column]
        #     transformed = [1/math.sqrt(x)-1 for x in data_norm]
        #     transformed_norm = [x / max(transformed) for x in transformed]
        #     return transformed_norm
        
        # def fahrdauer_norm(column):
        #     max_value = column.max()
        #     data_norm = [x / max_value for x in column]
        #     transformed = [1/math.sqrt(x)-1 for x in data_norm]
        #     transformed_norm = [x / max(transformed) for x in transformed]
        #     return transformed_norm
       
        
        gdf_WGS84_copy["kosten_norm"] = gdf_WGS84_copy.apply(kosten_norm, axis=1)
        gdf_WGS84_copy["ladeleistung_eff_norm"] = gdf_WGS84_copy.apply(ladeleistung_norm, axis=1)
        gdf_WGS84_copy["distanz_norm"] = gdf_WGS84_copy.apply(distanz_norm, axis=1)        
        gdf_WGS84_copy["fahrdauer_norm"] = gdf_WGS84_copy.apply(fahrdauer_norm, axis=1)
        # gdf_WGS84_copy["distanz_norm"] = distanz_norm(gdf_WGS84_copy[col_names["col_dist"]])        
        # gdf_WGS84_copy["fahrdauer_norm"] = fahrdauer_norm(gdf_WGS84_copy[col_names["col_fahrdauer"]])
                        
        # Kombination der normierten Werte zu einem gewichtetem Relevanzwert
        def relevanz_score(row):
            sum_score = row["kosten_norm"]*gewichtung_kosten + row["ladeleistung_eff_norm"]*gewichtung_ladeleistung + row["distanz_norm"]*gewichtung_distanz + row["fahrdauer_norm"]*gewichtung_fahrdauer
            sum_gewichtungen = gewichtung_kosten + gewichtung_ladeleistung + gewichtung_distanz + gewichtung_fahrdauer
            relevanz_score = (sum_score / sum_gewichtungen)*10
            return round(relevanz_score,1)
        
        gdf_WGS84_copy["relevanz_score"] = gdf_WGS84_copy.apply(relevanz_score, axis=1)
        
        df_relevanz_score = gdf_WGS84_copy[["relevanz_score", "Location_ID", "Plugs"]]
        df_relevanz_score_dict = pd.DataFrame(df_relevanz_score).to_dict("records")   
        station_relevance = gdf_WGS84_copy.sort_values("relevanz_score", ascending=False)
    
    
        # 5 Relevanzkategorien festlegen
        def relevanz_kategorien(row):
            relevanz = row["relevanz_score"]
            max_rel = max(station_relevance["relevanz_score"])
            min_rel = min(station_relevance["relevanz_score"])
            rel_range = max_rel - min_rel
            intervall = rel_range/5
            if relevanz <= min_rel + intervall:
                return 0
            elif relevanz <= min_rel + intervall*2:
                return 0.25
            elif relevanz <= min_rel + intervall*3:
                return 0.5
            elif relevanz <= min_rel + intervall*4:
                return 0.75
            else:
                return 1.0
               
        station_relevance["relevanz_kategorie"] = station_relevance.apply(relevanz_kategorien, axis=1)
        
        # Wenn nur verfügbare Ladestationen angezeigt werden sollen:
        if len(filter_verfuegbarkeit)>0 and filter_verfuegbarkeit[0] == "Nur verfügbare Ladestationen anzeigen":
            station_relevance = station_relevance.drop_duplicates(subset=["lon","lat"]) # Nur eine Lademöglichkeit pro Ladestation/Standort visualisieren
            # Karte erstellen
            fig = px.scatter_mapbox(station_relevance,
                                    lat=station_relevance["lat"],
                                    lon=station_relevance["lon"],
                                    color=station_relevance["relevanz_kategorie"],
                                    height = 585,
                                    width = 310,
                                    hover_data={"lat":False, "lon":False, "EVSEStatus":False},
                                    custom_data=["relevanz_kategorie"],
                                    color_continuous_scale=[(0, "rgba(50,50,50,0.1)"),(1.0,"rgba(0,0,0,1.0)")]
                                    )
        
        # wenn nicht nur verfügbare Ladestationen angezeigt werden sollen:
        else:
            # Aufteilen der Stationen nach Status (Verfügbarkeit)
            verfuegbare_stationen = station_relevance[(station_relevance["EVSEStatus"] == "Verfügbar")]
            verfuegbare_stationen = verfuegbare_stationen.drop_duplicates(subset=["lon","lat"])
            unbekannte_stationen = station_relevance[(station_relevance["EVSEStatus"] == "Unbekannt")]
            unbekannte_stationen = unbekannte_stationen.drop_duplicates(subset=["lon","lat"])
            besetzte_stationen = station_relevance[(station_relevance["EVSEStatus"] == "Besetzt")]
            besetzte_stationen_mask = ~besetzte_stationen["ChargingStationId"].isin(verfuegbare_stationen["ChargingStationId"]) # Nur Ladestationen, die komplett besetzt sind als besetzt anzeigen
            besetzte_stationen_clean = besetzte_stationen[besetzte_stationen_mask]
            besetzte_stationen_clean = besetzte_stationen_clean.drop_duplicates(subset=["lon","lat"])
            # Karte erstellen (mit verfügbaren Ladestationen)
            fig = px.scatter_mapbox(verfuegbare_stationen,
                                    lat=verfuegbare_stationen["lat"],
                                    lon=verfuegbare_stationen["lon"],
                                    color=verfuegbare_stationen["relevanz_kategorie"],
                                    height = 585,
                                    width = 310,
                                    hover_data={"lat":False, "lon":False, "EVSEStatus":False},
                                    custom_data=["relevanz_kategorie"],
                                    color_continuous_scale=[(0, "rgba(0,36,21,0.1)"),(1.0,"rgba(0,36,21,1.0)")]
                                    )
            # Besetzte Ladestationen und Ladestationen mit unbekannter Verfügbarkeit zur Karte hinzufügen
            fig.add_trace(go.Scattermapbox(lat=unbekannte_stationen["lat"],
                                           lon=unbekannte_stationen["lon"],
                                           mode="markers",
                                           marker=dict(color="orange")
                                           ))
            fig.add_trace(go.Scattermapbox(lat=besetzte_stationen_clean["lat"],
                                           lon=besetzte_stationen_clean["lon"],
                                           mode="markers",
                                           marker=dict(color="red")
                                           ))
            fig.data = fig.data[::-1]
        
        # Anpassungen an der Darstellung vornehmen
        fig.update_traces(marker=dict(size=14,allowoverlap=False), # Grösse der Marker festlegen
                          hovertemplate="<b><b><extra></extra>" # Hoverinformationen deaktivieren
                          )
        fig.update(layout_coloraxis_showscale=False) # Farblegende deaktivieren          
              
        # Position des Startorts berechnen und Punkt hinzufügen
        pos_start = gdf_positionen_WGS84[gdf_positionen_WGS84["orte"] == startort]
        x_pos_start = pos_start["geometry"].x
        y_pos_start = pos_start["geometry"].y
        fig.add_trace(go.Scattermapbox(lat=[float(y_pos_start)],
                                       lon=[float(x_pos_start)],
                                       mode="markers",
                                       name="position_start",
                                       marker=dict(size=16, color="blue")
                                       ))
        # Hoverinformationen für Startort festlegen
        fig.update_traces(hovertemplate=f'<b>Startort ({startort})<b><extra></extra>', selector={"name":"position_start"})
    
    # Wenn für die gewählten Filtereinstellungen keine Ladestation vorhanden ist
    else:
        # Karte mit Startort erstellen
        pos_start = gdf_positionen_WGS84[gdf_positionen_WGS84["orte"] == startort]
        x_pos_start = pos_start["geometry"].x
        y_pos_start = pos_start["geometry"].y
        # Karte erstellen
        fig = px.scatter_mapbox(gdf_positionen_WGS84,
                                lat=[float(y_pos_start)],
                                lon=[float(x_pos_start)],
                                height = 585,
                                width = 310)
        # Anpassungen vornehmen
        fig.update_traces(marker=dict(size=15,allowoverlap=False, color="blue"), hovertemplate=f'<b>Startort ({startort})<b><extra></extra>')
        # Titel setzen
        titel = "Keine Ladestationen zu diesen Filtereinstellungen gefunden!"
        df_relevanz_score_dict = dict()
        
    # Wenn Zielort definiert ist, dann Position des Zielorts berechnen und zur Karte hinzufügen
    if zielort is not None: 
        pos_end = gdf_positionen_WGS84[gdf_positionen_WGS84["orte"] == zielort]    
        x_pos_end = pos_end["geometry"].x
        y_pos_end = pos_end["geometry"].y
        fig.add_trace(go.Scattermapbox(lat=[float(y_pos_end)],
                                       lon=[float(x_pos_end)],
                                       mode="markers",
                                       name="position_end",
                                       marker=dict(size=15, color="yellow", symbol="circle")))
        fig.update_traces(hovertemplate=f'<b>Zielort ({zielort})<b><extra></extra>', selector= ({"name":"position_end"}))
       
    
    # Kartenmitte und Titel festlegen anhand der Art des Ladens
    if charging_mode == "Laden in der Nähe":
        pos_x = x_pos_start
        pos_y = y_pos_start
        z = 13
        if len(gdf_WGS84_copy.index) != 0:
            titel = "Ladestationen in der Nähe von " + startort
    elif charging_mode == "En-Route-Charging":
        pos_x = (float(x_pos_start) + float(x_pos_end))/2
        pos_y = (float(y_pos_start) + float( y_pos_end))/2
        z = 7
        titel = "Ladestationen auf dem Weg von " + startort + " nach " + zielort
    else:
        pos_x = x_pos_end
        pos_y = y_pos_end
        z = 13
        titel = "Ladestationen in der Nähe von " + zielort
    
    fig.update_layout(showlegend=False, mapbox=dict(center=dict(lat=float(pos_y), lon=float(pos_x)), zoom=z, uirevision= "foo"))
    
    # Layout anpassen
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig, df_relevanz_score_dict, titel


@app.callback(
    Output(component_id="id_informationen_ladestation", component_property="children"),
    Input(component_id="id_graph", component_property="clickData"),
    Input(component_id="id_gdf_filter", component_property="data"),
    Input(component_id="id_relevance_score", component_property="data"),
    Input(component_id="id_charging_mode", component_property="value"),
)
def click(clickData, gdf_WGS84_dict, df_relevanz_score_dict, charging_mode):
    if clickData != None and clickData["points"][0]["curveNumber"] < 4:
        try: 
            gdf_WGS84_copy = pd.DataFrame.from_dict(gdf_WGS84_dict)
            df_relevanz_score = pd.DataFrame.from_dict(df_relevanz_score_dict)
            gdf_WGS84_copy = pd.merge(gdf_WGS84_copy, df_relevanz_score, how="left", on=["Location_ID","Plugs"])
            lat_click = clickData["points"][0]["lat"]
            lon_click = clickData["points"][0]["lon"]
            ladestationen_ind = gdf_WGS84_copy[(gdf_WGS84_copy.lat == lat_click) & (gdf_WGS84_copy.lon == lon_click)].index[0:] # alle Ladestecker an dieser Ladestation bestimmen
            
            # Für jede Ladeoption an der Ladestation eine Übersicht erstellen
            if charging_mode == "En-Route-Charging":
                label_kosten = "Kosten pro kWh: "
                label_dauer = "Ladedauer 15 kWh:"
            else:
                label_kosten = "Kosten volladen: "
                label_dauer = "Dauer volladen: "
            
            beschreibungen = []          
            location_ids = {}
            for ind in ladestationen_ind:
                location_id = str(gdf_WGS84_copy.at[ind, "Location_ID"])
                if charging_mode == "En-Route-Charging":
                    kosten = str(round(float(gdf_WGS84_copy.at[ind, "Kosten"])/15,2)) # Kosten für das Laden von 15 kWh (bei en-route charging)
                else:
                    kosten = str(gdf_WGS84_copy.at[ind, "Kosten"]) # Kosten für das Laden in der Nähe des Start- oder Zielorts
                
                # Definieren der Informationen zu den Ladestationen
                if location_id not in location_ids:
                    location_ids[location_id] = []
                    # Relevanzwert der Ladestation
                    relevance_score = gdf_WGS84_copy.at[ind, "relevanz_score"]
                    # erste Spalte mit Status, Steckertyp, Attributnamen (Ladeleistung eff. Ladekosten, Ladedauer)
                    col1 = [str(gdf_WGS84_copy.at[ind, "EVSEStatus"]), str(gdf_WGS84_copy.at[ind, "Plugs"]), "Ladeleistung max.:", label_kosten, label_dauer]
                    # zweite Spalte mit Werten zur Ladeleistung, Ladeleistung eff., Ladekosten und Ladedauer
                    col2 = [".", str(gdf_WGS84_copy.at[ind, "power"]) + " kW", str(gdf_WGS84_copy.at[ind, "ladeleistung_eff"]) + " kW", kosten + " CHF", str(gdf_WGS84_copy.at[ind, "ladedauer"]) + " min"]
                    # Sammeln der Informationen zur Ladestation in einer Liste
                    beschreibung_list = [relevance_score, col1, col2, location_id]
                    # Sammeln der Informationen zu allen Ladestationen an einem bestimmten Standort (ein POI kann für mehrere Ladestationen stehen)
                    beschreibungen.append(beschreibung_list)
                    location_ids[location_id] = beschreibung_list
                
                # Falls an einer Ladestation unterschiedliche Steckertypen mit unterschiedlichen Ladeleistungen verwendet werden können, werden die Informationen zu den anderen Lademöglichkeiten ebenfalls integriert
                else:
                    # Anpassen der Informationen zur Ladeleistung und des Steckertyps
                    end_power = location_ids[location_id][2][1].find(" kW")
                    location_ids[location_id][2][1] = location_ids[location_id][2][1][:end_power] + "/" + str(gdf_WGS84_copy.at[ind, "power"]) + " kW"
                    location_ids[location_id][1][1] = location_ids[location_id][1][1] + "/" + str(gdf_WGS84_copy.at[ind, "Plugs"])
                    
                    # Anpassen der Informationen zur Ladeleistung eff.
                    end_ladeleistung = location_ids[location_id][2][2].find(" kW")
                    if location_ids[location_id][2][2][:end_ladeleistung] != str(gdf_WGS84_copy.at[ind, "ladeleistung_eff"]):
                        location_ids[location_id][2][2] =  location_ids[location_id][2][2][:end_ladeleistung] + "/" + str(gdf_WGS84_copy.at[ind, "ladeleistung_eff"]) + " kW"
                    
                    # Anpassen der Informationen zu den Kosten
                    end_kosten = location_ids[location_id][2][3].find(" CHF")
                    if location_ids[location_id][2][3][:end_kosten] != kosten:
                        location_ids[location_id][2][3] =  location_ids[location_id][2][3][:end_kosten] + "/" + kosten + " CHF"
                    
                    # Anpassen der Informationen zu der Ladedauer
                    end_ladedauer = location_ids[location_id][2][4].find(" min")
                    if location_ids[location_id][2][4][:end_ladedauer] != str(gdf_WGS84_copy.at[ind, "ladedauer"]):
                        location_ids[location_id][2][4] =  location_ids[location_id][2][4][:end_ladedauer] + "/" + str(gdf_WGS84_copy.at[ind, "ladedauer"]) + " min"
                    
            beschreibungen_sorted = sorted(beschreibungen, reverse=True)
            
            # Style der Informationsboxen anpassen
            list_of_cards = [html.P("Informationen zur Ladestation", style={"font-weight":"bold", "margin-bottom":"2px", "margin-top":"0px"})]
            for b in beschreibungen_sorted:
                col1_str = "\n".join(b[1])
                col2_str = "\n".join(b[2])
                if b[1][0] == "Verfügbar":
                    color = "#198754"
                    inverse = True
                if b[1][0] == "Besetzt":
                    color="#dc3545"
                    inverse = True
                if b[1][0] == "Unbekannt":
                    color="light"
                    inverse = False
                list_of_cards.append(dbc.Card(dbc.CardBody([dbc.Row([dbc.Col(dcc.Markdown(children="**"+ str(b[0])+"**", style={"white-space":"pre", "margin-bottom":"0px"}),align="center", width=1, style={"margin-right":"8px"}), dbc.Col(dcc.Markdown(children=col1_str, style={"white-space":"pre", "margin-bottom":"0px"})), dbc.Col(dcc.Markdown(children=col2_str,style={"white-space":"pre", "margin-bottom":"0px"}))])]),color=color, inverse=inverse))
                
            list_of_cards.append(html.P(str(gdf_WGS84_copy.at[ladestationen_ind[0], "OperatorName"]), style={"margin-bottom":"0px"}))
            
            # Unterhalb der Informationsboxen Informationen zur Adresse und dem Ladenetzwerk hinzufügen
            try:
                adresse = str(gdf_WGS84_copy.at[ladestationen_ind[0], "Adresse"])
                strasse = adresse.split(",")[0]
                ort = ",".join(adresse.split(",")[1:])
                list_of_cards.append(html.P(strasse + ",", style={"margin-top":"0px", "margin-bottom":"0px"}))
                list_of_cards.append(html.P(ort, style={"margin-top":"0px", "margin-bottom":"0px"}))
            except:
                list_of_cards.append(str(gdf_WGS84_copy.at[ladestationen_ind[0], "Adresse"]))
            
            informationen = list_of_cards
            
            return informationen
        
        # Falls etwas beim erstellen der Informationsboxen fehlschlägt:
        except:
            # Wenn keine Ladestationen vorhanden ist
            if len(df_relevanz_score_dict) == 0:
                return "Keine Ladestation für diese Filtereinstellungen gefunden"
            # Wenn Start- oder Zielort angeklickt wird
            else:
                return "Wählen sie eine Ladestation"
    # wenn noch kein POI angeklickt wurde
    else:
        return "Wählen sie eine Ladestation"


if __name__=='__main__':
    app.run_server(debug=True, port=8051)
    
