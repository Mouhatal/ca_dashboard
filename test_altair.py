import altair as alt
from vega_datasets import data

source = data.cars()

alt.Chart(source).mark_circle(size=60).encode(
    x='Horsepower',
    y='Miles_per_Gallon',
    color='Origin',
    tooltip=['Name', 'Origin', 'Horsepower', 'Miles_per_Gallon']
).interactive()



import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime
from data_loader import load_data
from utils import merge_data, filter_data

#######################
# Page configuration
st.set_page_config(
    page_title='Analyse des Activités',
    page_icon=':bar_chart:',
    layout='wide',
    initial_sidebar_state='expanded'
)

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown("""
<style>
[data-testid="block-container"] {
    padding: 2rem 1rem 1rem 1rem;
}
[data-testid="stVerticalBlock"] {
    padding: 0;
}
[data-testid="stMetric"] {
    background-color: #f0f2f6;
    text-align: center;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

#######################
# Load data
villages, activities = load_data()
if villages is None or activities is None:
    st.error("Impossible de charger les données.")
    st.stop()

# Fusion des données
data = merge_data(villages, activities)
if data is None:
    st.error("La fusion des données a échoué.")
    st.stop()

# Vérification et ajout des colonnes latitude et longitude si elles n'existent pas
if 'latitude' not in data.columns or 'longitude' not in data.columns:
    data['latitude'] = 15.0 + (data.index % 10) * 0.1
    data['longitude'] = -15.0 - (data.index % 10) * 0.1

#######################
# Sidebar
with st.sidebar:
    st.title('Analyse des Activités')
    
    zone = st.selectbox('Zone', options=[None] + list(data['ZONE'].unique()))
    sexe = st.radio('Sexe', options=[None, 'M', 'F'], index=0, key='sexe_filter')
    age_group = st.selectbox("Tranche d'âge", options=[None, '-18', '18-24', '25-35', '35+'], key='age_filter')
    activity_type = st.selectbox('Type d\'activité', options=[None] + list(data['Activité'].unique()), key='activity_type_filter')
    
    min_date = pd.Timestamp(data['Date'].min())
    max_date = pd.Timestamp(data['Date'].max())
    start_date, end_date = st.slider('Sélectionner une plage de dates',
                                     min_value=min_date.to_pydatetime(),
                                     max_value=max_date.to_pydatetime(),
                                     value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
                                     format="MMM YYYY")

# Filtrer les données
filtered_data = filter_data(data, zone, None, sexe, age_group, activity_type, start_date, end_date)

#######################
# Dashboard Main Panel

st.markdown("# CorpsAfrica/Sénégal : Dashboard Novembre à Avril")

# Row 1: Main metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Villages", 51)
col2.metric("Communes", 19)
col3.metric("Départements", 11)
col4.metric("Nombre de Régions", 9)

# Row 2: Maps and Charts
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Répartition des Volontaires au Sénégal")
    m = folium.Map(location=[14.4974, -14.4524], zoom_start=6)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in filtered_data.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"Village: {row['Régions']}<br>Activité: {row['Activité']}<br>Total Bénéficiaires: {row['Total Beneficiaire']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(marker_cluster)

    st_folium(m, width=700, height=500)

with col2:
    st.markdown("### Répartition des Volontaires par Sexe")
    pie_data = filtered_data[['M', 'F']].sum().reset_index()
    pie_data.columns = ['Sexe', 'Total Beneficiaire']
    pie_data['Sexe'] = pie_data['Sexe'].apply(lambda x: 'Masculin' if x == 'M' else 'Féminin')
    fig_pie = px.pie(pie_data, values='Total Beneficiaire', names='Sexe', title='Répartition par Sexe')
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("### Répartition des Volontaires par Région")
    region_data = filtered_data.groupby('Régions')['Total Beneficiaire'].sum().reset_index()
    fig_region = px.bar(region_data, x='Régions', y='Total Beneficiaire', title='Répartition par Région')
    st.plotly_chart(fig_region, use_container_width=True)

# Row 3: Activity and Beneficiaries
col1, col2 = st.columns([1, 1])
col1.metric("Sections d'Activités", 15)
col1.metric("Activités", 604)
col2.metric("Bénéficiaires Directs", "38K")
col2.metric("Bénéficiaires Indirects", "75K")

# Row 4: Detailed Charts
st.markdown("### Total Bénéficiaires par Secteur d'Activité")
activity_sector = filtered_data.groupby('Activité')['Total Beneficiaire'].sum().reset_index()
fig_activity = px.bar(activity_sector, x='Activité', y='Total Beneficiaire', title='Total Bénéficiaires par Activité')
st.plotly_chart(fig_activity, use_container_width=True)

st.markdown("### Total Bénéficiaires par Mois")
aggregated_monthly_data = filtered_data.groupby(filtered_data['Date'].dt.to_period('M')).sum().reset_index()
aggregated_monthly_data['Date'] = aggregated_monthly_data['Date'].astype(str)
fig_monthly = px.line(aggregated_monthly_data, x='Date', y='Total Beneficiaire', title='Total Bénéficiaires par Mois')
st.plotly_chart(fig_monthly, use_container_width=True)

#######################
# Footer
footer_html = """<div style='text-align: center;'>
  <p>Developed with ❤️ by 
<a href="https://www.linkedin.com/in/mouhamadou-tall/">Mouhamadou TALL</a></p>
</div>"""
st.markdown(footer_html, unsafe_allow_html=True)

hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)




