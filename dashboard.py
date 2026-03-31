import os
import streamlit as st
if "KAGGLE_API_TOKEN" in st.secrets:
    os.environ["KAGGLE_API_TOKEN"] = st.secrets["KAGGLE_API_TOKEN"]

import streamlit as st
import geopandas as gpd
import pandas as pd
import json
import folium
import re
import requests
import warnings
from folium import Tooltip
import kagglehub
from kagglehub import KaggleDatasetAdapter

warnings.filterwarnings("ignore")

################
##  Functions  ##
################

def clean_data(input_df, parameter, length=2):
    """Standardizes codes to ensure leading zeros (e.g., '1' -> '01')."""
    input_df = input_df.copy()
    input_df[parameter] = input_df[parameter].astype(str).str.strip().str.zfill(length)
    return input_df

@st.cache_data
def load_base_data():
    df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "clementh7/france-immigration-2018-2021",
        "merged_clean.csv",
        pandas_kwargs={"delimiter": ";"}
    )
    df['CODGEO'] = df['CODGEO'].astype(str).str.zfill(5)
    return df

@st.cache_data
def fetch_geojson(url, code_len):
    """
    Fixed version: Uses requests to bypass the fiona.path AttributeError 
    common in some geopandas/fiona version mismatches.
    """
    response = requests.get(url)
    data = response.json()
    gdf = gpd.GeoDataFrame.from_features(data["features"])
    # Set the CRS explicitly to WGS84
    gdf.set_crs(epsg=4324, inplace=True)
    
    # Standardize 'code' column
    if 'code' in gdf.columns:
        gdf['code'] = gdf['code'].astype(str).str.zfill(code_len)
    
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
    return gdf

def make_map(input_df, geo_gdf, column_name, legend_title):
    # 1. Create a lookup dictionary for fast access: { 'code': percentage_value }
    # We use 'pct' as the key because that's what we calculated in the main logic
    data_lookup = input_df.set_index('code')[column_name].to_dict()
    
    # 2. Inject the percentage into the GeoJSON properties
    # This ensures the tooltip can 'see' the number
    geo_json_data = json.loads(geo_gdf.to_json())
    for feature in geo_json_data['features']:
        geo_code = feature['properties']['code']
        # Assign the percentage if it exists, otherwise 'N/A'
        feature['properties']['display_pct'] = f"{round(data_lookup.get(geo_code, 0), 2)}%"

    # 3. Initialize Map
    m = folium.Map(location=[46.2276, 2.2137], zoom_start=6, tiles='CartoDB positron')
    
    # 4. Choropleth Layer
    folium.Choropleth(
        geo_data=geo_json_data, # Use the injected data here
        data=input_df,
        columns=['code', column_name],
        key_on='feature.properties.code',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_title,
        nan_fill_color='white'
    ).add_to(m)

    # 5. Tooltip Layer 
    folium.GeoJson(
        geo_json_data,
        style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
        tooltip=folium.GeoJsonTooltip(
            fields=['nom', 'code', 'display_pct'],
            aliases=['Name:', 'Dept/Commune Code:', 'Value:'],
            localize=True,
            sticky=False
        )
    ).add_to(m)
    
    return m

    
    def style_fn(feature):
        return {'fillColor': '#ffffff00', 'color': '#ffffff00'}

    # Add invisible GeoJson layer for tooltips to keep it snappy
    folium.GeoJson(
        geo_gdf,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=['code', 'nom'],
            aliases=['Code:', 'Name:'],
            localize=True
        )
    ).add_to(m)
    
    return m

@st.cache_data
def assign_pol_group(nom):
    # Standardizing names to uppercase to ensure matching works
    nom = str(nom).upper()
    ex_droite = ['ZEMMOUR', 'LE PEN', 'DUPONT-AIGNAN']
    droite = ['PÉCRESSE', 'BERTRAND']
    centre = ['MACRON']
    gauche = ['JADOT', 'HIDALGO']
    ex_gauche = ['MÉLENCHON', 'ROUSSEL', 'ARTHAUD', 'POUTOU']  
    
    if nom in ex_droite: return 1
    elif nom in droite: return 2
    elif nom in centre: return 3
    elif nom in gauche: return 4
    elif nom in ex_gauche: return 5
    else: return 6

@st.cache_data
def calculate_population_difference(input_df, selected_year, selected_scale, geojson_selected_scale):
    selected_year = int(selected_year)  # ensure int regardless of selectbox string input

    year_column                    = f'NB_{selected_year}'
    previous_year_column           = f'NB_{selected_year - 1}'
    year_total_population_column   = f"total_population_{selected_year}"
    previous_total_population_column = f"total_population_{selected_year - 1}"
    diff_col = f'population_diff_{selected_year - 1}_{selected_year}'

    input_df = input_df.copy()
    input_df = clean_data(input_df, 'CODGEO')

    pop_diff = input_df.groupby(['CODGEO', 'IMMI'])[[year_column, previous_year_column]].sum().reset_index()
    pop_diff[year_total_population_column]      = pop_diff.groupby('CODGEO')[year_column].transform('sum')
    pop_diff[previous_total_population_column]  = pop_diff.groupby('CODGEO')[previous_year_column].transform('sum')
    pop_diff = pop_diff[pop_diff['IMMI'] == 1].copy()

    pop_diff[diff_col] = pop_diff[year_total_population_column] - pop_diff[previous_total_population_column]
    pop_diff = pop_diff[['CODGEO', diff_col, year_total_population_column]]

    pop_diff = clean_data(pop_diff, 'CODGEO')
    pop_diff[diff_col]                        = pop_diff[diff_col].round(2)
    pop_diff[year_total_population_column]    = pop_diff[year_total_population_column].round(2)

    if selected_scale == 'departements':
        pop_diff['CODGEO'] = pop_diff['CODGEO'].astype(str).str[:2]

    pop_diff = geojson_selected_scale.merge(
        pop_diff[['CODGEO', diff_col, year_total_population_column]],
        left_on='code', right_on='CODGEO'
    ).sort_values(by=diff_col, ascending=False)

    return pop_diff

######################
##    Main App      ##
######################

st.set_page_config(page_title="France Data Dashboard", layout="wide")

# Data loading
df = load_base_data()
dep_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson"
com_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson"

tab1, tab2 = st.tabs(["Immigration Statistics", "Election Analysis"])

# --- TAB 1: IMMIGRATION ---
with tab1:
    with st.sidebar:
        st.header("Global Filters")
        year_cols = [col for col in df.columns if col.startswith('NB_')]
        year_list = sorted([c.split('_')[1] for c in year_cols], reverse=True)
        sel_year = st.selectbox('Select Year', year_list)
        sel_scale = st.selectbox('Geographic Scale', ['Departements', 'Communes'])
        
        # Pre-load Dept GeoJSON for selection and mapping
        dept_gdf = fetch_geojson(dep_url, 2)
        
    curr_col = f"NB_{sel_year}"
    
    if sel_scale == 'Departements':
        # Process data at Department level
        working_df = df.copy()
        working_df['dept_code'] = working_df['CODGEO'].str[:2]
        
        # Group by Dept and Immigration status
        agg = working_df.groupby(['dept_code', 'IMMI'])[curr_col].sum().reset_index()
        total_pop = agg.groupby('dept_code')[curr_col].transform('sum')
        agg['pct'] = (agg[curr_col] / total_pop) * 100
        
        # Filter for Immigrants and ensure code match
        immi_stats = agg[agg['IMMI'] == 1].copy()
        immi_stats['code'] = immi_stats['dept_code'].str.zfill(2)
        
        # Merge with names for the legend/tooltip
        final_df = immi_stats.merge(dept_gdf[['code', 'nom']], on='code', how='inner')
        map_bg = dept_gdf
    else:
        # Commune scale: Must filter by Dept to avoid memory errors
        dept_names = sorted(dept_gdf['nom'].unique())
        sel_dept = st.sidebar.selectbox("Filter by Department", dept_names)
        target_code = dept_gdf[dept_gdf['nom'] == sel_dept]['code'].values[0]
        
        # Load Communes for that specific Dept
        com_gdf = fetch_geojson(com_url, 5)
        map_bg = com_gdf[com_gdf['code'].str.startswith(target_code)].copy()
        
        # Filter raw data
        commune_data = df[df['CODGEO'].str.startswith(target_code)].copy()
        agg = commune_data.groupby(['CODGEO', 'IMMI'])[curr_col].sum().reset_index()
        total_pop = agg.groupby('CODGEO')[curr_col].transform('sum')
        agg['pct'] = (agg[curr_col] / total_pop) * 100
        
        immi_stats = agg[agg['IMMI'] == 1].copy()
        immi_stats['code'] = immi_stats['CODGEO'].str.zfill(5)
        
        final_df = immi_stats.merge(map_bg[['code', 'nom']], on='code', how='inner')

    # Visuals
    col_map, col_stats = st.columns([3, 1])
    with col_map:
        st.subheader(f"Percentage of Born Non-French residents in {sel_year}")
        if not final_df.empty:
            m1 = make_map(final_df, map_bg, 'pct', "Immigrant %")
            st.components.v1.html(m1._repr_html_(), height=600)
        else:
            st.error("No data found for this selection.")
            
    with col_stats:
        st.markdown('#### Highest Rates')
    
        percentage_column = f"percentage_migrants_{sel_year}"
        df_selected_year_sorted = final_df.sort_values(by='pct', ascending=False)
    
        st.dataframe(
            df_selected_year_sorted,
            column_order=("nom", "pct"),
            hide_index=True,
            column_config={
                "nom": st.column_config.TextColumn(label="Area"),
                "pct": st.column_config.ProgressColumn(
                    label="Percentage",
                    format="%.2f%%",
                    min_value=0,
                    max_value=float(df_selected_year_sorted['pct'].max()),
                )
            }
        )

    with st.expander('About', expanded=False):
        st.write('''
            - Data: [INSEE] Nationalité et Immigration : Recensement de la population [IMG1A](<https://www.insee.fr/fr/statistiques/8202714?sommaire=8202756#consulter>)
            - :red[**Immigrant**]: According to the definition adopted by the High Council for Integration, an immigrant is a person born abroad and living in France. [See more](<https://www.insee.fr/fr/information/2383278#def_I>).
            - :orange[**Gains/Losses**]: Areas with the highest difference between selected year and the year before; the figure above is the total population of the area.
        ''')

# --- TAB 2: ELECTIONS ---
with tab2:
    st.header('2022 Presidential Election Results')

    with st.sidebar:
        st.header("Election Filters")
        selected_round = st.radio("Round", ["First Round", "Second Round"], horizontal=True)
        sel_scale_elec = st.selectbox('Geographic Scale ', ['Departements', 'Communes'])

    # Map round selection to Kaggle dataset paths
    suffix = "t1" if selected_round == "First Round" else "t2"
    k_path = f"clementh7/election-presidentielle-{'premier' if suffix == 't1' else 'deuxime'}-tour-2022"

    try:
        elec_raw = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            k_path,
            f'presidentielle-2022-communes-{suffix}.csv'
        )

        if 'nom' in elec_raw.columns:
            elec_raw['pol_group'] = elec_raw['nom'].apply(assign_pol_group)

        st.success(f"Successfully loaded {len(elec_raw)} rows of election data.")

        # Identify the commune name column
        group_col = 'libelle_commune' if 'libelle_commune' in elec_raw.columns else 'nom_commune'

        # Pre-load département GeoJSON
        dept_gdf_elec = fetch_geojson(dep_url, 2)

        if sel_scale_elec == 'Departements':
            elec_raw['full_code'] = (
                elec_raw['code_departement'].astype(str).str.zfill(2) +
                elec_raw['code_commune'].astype(str).str.zfill(3)
            )
            elec_raw['dept_code'] = elec_raw['code_departement'].astype(str).str.zfill(2)
        
            agg = elec_raw.groupby(['dept_code', 'pol_group'])['voix'].sum().reset_index()
            total_votes = agg.groupby('dept_code')['voix'].transform('sum')
            agg['pct'] = (agg['voix'] / total_votes) * 100
        
            elec_ex_r = agg[agg['pol_group'] == 1].copy()
            elec_ex_r['code'] = elec_ex_r['dept_code'].str.zfill(2)
        
            final_elec_df = elec_ex_r.merge(dept_gdf_elec[['code', 'nom']], on='code', how='inner')
            map_bg_elec = dept_gdf_elec
        
        else:
            dept_names_elec = sorted(dept_gdf_elec['nom'].unique())
            sel_dept_elec = st.sidebar.selectbox("Filter by Department ", dept_names_elec)
            target_code_elec = dept_gdf_elec[dept_gdf_elec['nom'] == sel_dept_elec]['code'].values[0]
        
            com_gdf_elec = fetch_geojson(com_url, 5)
            map_bg_elec = com_gdf_elec[com_gdf_elec['code'].str.startswith(target_code_elec)].copy()
        
            elec_raw['full_code'] = (
                elec_raw['code_departement'].astype(str).str.zfill(2) +
                elec_raw['code_commune'].astype(str).str.zfill(3)
            )
            commune_elec = elec_raw[elec_raw['full_code'].str.startswith(target_code_elec)].copy()
        
            agg = commune_elec.groupby(['full_code', 'pol_group'])['voix'].sum().reset_index()
            total_votes = agg.groupby('full_code')['voix'].transform('sum')
            agg['pct'] = (agg['voix'] / total_votes) * 100
        
            elec_ex_r = agg[agg['pol_group'] == 1].copy()
            elec_ex_r['code'] = elec_ex_r['full_code'].str.zfill(5)
        
            final_elec_df = elec_ex_r.merge(map_bg_elec[['code', 'nom']], on='code', how='inner')
        
        final_elec_df = final_elec_df.dropna(subset=['pct'])

        # Map and table
        col_map_elec, col_stats_elec = st.columns([3, 1])

        with col_map_elec:
            st.subheader(f"Extreme Right Vote Share — {selected_round}")
            if not final_elec_df.empty:
                m2 = make_map(final_elec_df, map_bg_elec, 'pct', "Extreme Right %")
                st.components.v1.html(m2._repr_html_(), height=600)
            else:
                st.error("No data found for this selection.")

        with col_stats_elec:
            st.markdown('#### Highest Rates')
            st.dataframe(
                final_elec_df[['nom', 'pct']].sort_values('pct', ascending=False),
                hide_index=True,
                column_config={
                    "nom": st.column_config.TextColumn(label="Area"),
                    "pct": st.column_config.ProgressColumn(
                        label="Extreme Right %",
                        format="%.2f%%",
                        min_value=0,
                        max_value=float(final_elec_df['pct'].max()),
                    )
                }
            )

    except Exception as e:
        st.error(f"Election data could not be loaded: {e}")
