import streamlit as st
import os
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Paths (ensure these paths are correct)
main_path = os.path.abspath(os.getcwd())  # Main directory
data_path = os.path.join(main_path, 'data', 'processed')  # Data directory
shp_path = os.path.join(data_path, 'shp')  # Shape directory
mpio_path = os.path.join(data_path, 'mpio_cluster.csv')  # Municipality data
ent_path = os.path.join(data_path, 'ent_cluster.csv')  # State data
shp_ent_path = os.path.join(shp_path, 'shp_ent_tidy_data.shp')  # Shape of states
shp_mpio_path = os.path.join(shp_path, 'shp_mun_tidy_data.shp')  # Shape of municipalities
mxn_gdf_path = os.path.join(shp_path, 'dest_2010cw.shp')  # Shape of all Mexico

# Load data
mpio_data = pd.read_csv(mpio_path, dtype={'cvegeo': str})          
ent_data = pd.read_csv(ent_path, dtype={'cvegeo': str})            

mpio_gdf = gpd.read_file(shp_mpio_path)     
ent_gdf = gpd.read_file(shp_ent_path)       
ent_gdf['cvegeo'] = ent_gdf['cvegeo'].astype(str)

mxn_gdf = gpd.read_file(mxn_gdf_path)       

# Add year selection
st.title("Mapa interactivo de México")

# Year selection using radio buttons
st.markdown("<h3>Selecciona el año:</h3>", unsafe_allow_html=True)
selected_year = st.radio("Selecciona el año", [2018, 2020, 2022], horizontal=True, label_visibility="collapsed")

# Filter ent_data by selected year
ent_year = ent_data[ent_data['Año'] == selected_year]

# Filter mpio_data by selected year
mpio_year = mpio_data[mpio_data['Año'] == selected_year]

# Merge filtered entity data with GeoDataFrame
ent_merged = ent_gdf.merge(ent_year, on='cvegeo', how='inner')

# Merge filtered mpio data with GeoDataFrame
mpio_merged = mpio_gdf.merge(mpio_year, on='cvegeo', how='inner')

# Add a toggle to select between viewing states, municipalities, or neither
vista_seleccionada = st.radio(
    "Selecciona la vista",
    ["Vista individual de estado/municipio", "Vista de todos los estados", "Vista de todos los municipios"],
    index=0  # Default selection
)

# Create a base map centered on Mexico
map_center = [23.634915, -102.552784]  # Coordinates of Mexico
m = folium.Map(location=map_center, zoom_start=5)

# If the user wants to see all states and there's an existing HTML map
if vista_seleccionada == "Vista de todos los estados":
    # Path to the pre-generated HTML map
    html_map_path = os.path.join(data_path, 'maps', f'{selected_year}_ent_map.html')
    if os.path.exists(html_map_path):
        # Load the pre-generated HTML map
        with open(html_map_path, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()
        st.components.v1.html(html_content, height=600, width=800)
        st.write("Mostrando todos los estados de México")

elif vista_seleccionada == "Vista de todos los municipios":
    # Path to the pre-generated HTML map
    html_map_path = os.path.join(data_path, 'maps', f'{selected_year}_mpio_map.html')
    if os.path.exists(html_map_path):
        # Load the pre-generated HTML map
        with open(html_map_path, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()
        st.components.v1.html(html_content, height=600, width=800)
        st.write("Mostrando todos los municipios de México con datos")
else:
    # Dropdown to select a state
    estado_seleccionado = st.selectbox('Selecciona un estado:', ent_gdf['nom_geo'].unique())

    # Get the cvegeo of the selected state
    estado_cvegeo = ent_gdf.loc[ent_gdf['nom_geo'] == estado_seleccionado, 'cvegeo'].values[0]
    
    # Filter municipalities for the selected state
    municipios_filtrados = mpio_year[mpio_year['estado_codigo'] == int(estado_cvegeo)]

    # Merge filtered data with GeoDataFrame
    mpio_merged = mpio_gdf.merge(municipios_filtrados, on='cvegeo', how='inner')

    # Toggle for municipality view
    vista_municipios = st.checkbox(f"Vista de municipios validos de {estado_seleccionado}", value=False)

    if vista_municipios:
        # View by municipalities: plot filtered municipalities in blue
        folium.GeoJson(
            mpio_merged,
            style_function=lambda x: {
                'fillColor': 'green',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.5
            },
            tooltip=folium.GeoJsonTooltip(fields=['Año', 'Estado', 'nom_geo', 'GINI', 'Ingreso promedio total'], aliases=['Año', 'Estado', 'Municipio', 'Índice Gini', 'Ingreso promedio'])
        ).add_to(m)
        st.write(f"Mostrando la vista por municipios del estado: {estado_seleccionado}")
    else:
        # View by state: plot the full state in green
        estado_seleccionado_gdf = ent_merged[ent_merged['cvegeo'] == estado_cvegeo]
        folium.GeoJson(
            estado_seleccionado_gdf,
            style_function=lambda x: {
                'fillColor': 'green',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.5
            },
            tooltip=folium.GeoJsonTooltip(fields=['Año', 'nom_geo', 'GINI', 'Ingreso promedio total'], aliases=['Año', 'Estado', 'Índice Gini', 'Ingreso promedio'])
        ).add_to(m)
        st.write(f"Mostrando la vista del estado completo: {estado_seleccionado}")

# Display the map in Streamlit
st_folium(m, width=700, height=500)
