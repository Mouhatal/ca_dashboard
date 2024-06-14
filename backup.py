
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objs as go
import folium
from streamlit_folium import st_folium
from data_loader import load_data  # Assurez-vous que ce module est correct
from utils import merge_data, filter_data  # Assurez-vous que ce module est correct
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title='Analyse des Activités',
    page_icon=':bar_chart:',
    
)
st.image('assets/logo_CA-removebg-preview.png', width=100)

# Titre principal centré avec une icône
st.markdown("<h1 style='text-align: center;'>Analyse des Activités</h1>", unsafe_allow_html=True)

# Chargement des données
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
    # Ajouter des coordonnées fictives pour l'exemple
    data['latitude'] = 15.0 + (data.index % 10) * 0.1
    data['longitude'] = -15.0 - (data.index % 10) * 0.1

# Afficher les colonnes disponibles (décommenter si nécessaire)
# st.write("Colonnes disponibles après fusion:", data.columns)

st.sidebar.markdown("""
Ce tableau de bord présente une analyse des activités avec un focus sur les bénéficiaires.

Contactez-nous pour plus d'informations :
- [CorpsAfrica/Sénégal](https://www.corpsafrica.org/where-we-work/senegal/)
- Téléphone : [+221 77 00 00 00](tel:+221770000000)
- Email : [QgqFP@example.com](mailto:QgqFP@example.com)
""")
# Filtres
st.sidebar.header('Filtres')
zone = st.sidebar.selectbox('Zone', options=[None] + list(data['ZONE'].unique()))
sexe = st.sidebar.radio('Sexe', options=[None, 'M', 'F'], index=0, key='sexe_filter')
age_group = st.sidebar.selectbox("Tranche d'âge", options=[None, '-18', '18-24', '25-35', '35+'], key='age_filter')
activity_type = st.sidebar.selectbox('Type d\'activité', options=[None] + list(data['Activité'].unique()), key='activity_type_filter')


# Sélection de la plage de dates avec un slider
min_date = pd.Timestamp(data['Date'].min())
max_date = pd.Timestamp(data['Date'].max())
# Slider vertical pour la sélection de dates
start_date, end_date = st.sidebar.slider('Sélectionner une plage de dates',
                                         min_value=min_date.to_pydatetime(),
                                         max_value=max_date.to_pydatetime(),
                                         value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
                                         format="MMM YYYY")

# Filtrer les données
filtered_data = filter_data(data, zone, None, sexe, age_group, activity_type, start_date, end_date)

# Affichage des données filtrées (décommenter si nécessaire)
# st.header('Données Filtrées')
# st.write(filtered_data)
# Afficher les métriques globales
#st.markdown("### Métriques Globales")
#col1, col2, col3, col4 = st.columns(4)
#with col1:
#    st.metric("Secteurs d'activités", total_sectors)
#with col2:
 #   st.metric("Activités", total_activities)
#with col3:
 #   st.metric("Bénéficiaires directs", beneficiaries_direct)
#with col4:
 #   st.metric("Bénéficiaires indirects", beneficiaries_indirect)
# Calculer les totaux pour les métriques globales
total_activities = filtered_data['Activité'].nunique()
total_beneficiaries = filtered_data['Total Beneficiaire'].sum()
total_sectors = filtered_data['Activité'].nunique()
beneficiaries_direct = total_beneficiaries  # Adapter si nécessaire
beneficiaries_indirect = total_beneficiaries * 10  # Exemple de multiplicateur

# Afficher les métriques globales
st.markdown("### Métriques Globales")
col1, col2 = st.columns(2)
with col1:
    st.metric("Activités", total_activities)
with col2:
    st.metric("Bénéficiaires directs", beneficiaries_direct)
# with col3:
#     st.metric("Bénéficiaires indirects", beneficiaries_indirect)

# Graphiques
if not filtered_data.empty:
    # Total bénéficiaires par activité
    fig_activities = px.bar(filtered_data, x='Activité', y='Total Beneficiaire', title='Total Bénéficiaires par Activité')
    st.plotly_chart(fig_activities)
    
    # Agréger les bénéficiaires par date
    aggregated_data = filtered_data.groupby('Date')[['Total Beneficiaire', 'M', 'F']].sum().reset_index()

    # Graphique de l'évolution des bénéficiaires par date avec étiquettes
    fig_beneficiaries = px.line(aggregated_data, x='Date', y='Total Beneficiaire', title='Évolution du nombre total de bénéficiaires par date',
                                labels={'Date': 'Date', 'Total Beneficiaire': 'Nombre total de bénéficiaires'},
                                text='Total Beneficiaire')  # Utilisation de 'text' pour afficher les valeurs sur le graphique

    fig_beneficiaries.update_traces(textposition='top center')  # Position des étiquettes

    st.plotly_chart(fig_beneficiaries)

   
        
    # Diagramme circulaire du total de bénéficiaires par sexe
    pie_data = filtered_data[['M', 'F']].sum().reset_index()
    pie_data.columns = ['Sexe', 'Total Beneficiaire']
    pie_data['Sexe'] = pie_data['Sexe'].apply(lambda x: 'Masculin' if x == 'M' else 'Féminin')

    fig_pie = px.pie(pie_data, values='Total Beneficiaire', names='Sexe', title='Répartition du total des bénéficiaires par sexe')
    st.plotly_chart(fig_pie)
    
   
    # Agrégation par mois
    aggregated_monthly_data = filtered_data.groupby(filtered_data['Date'].dt.to_period('M')).sum().reset_index()

    # Convertir les périodes en chaînes de caractères pour rendre les données sérialisables en JSON
    aggregated_monthly_data['Date'] = aggregated_monthly_data['Date'].astype(str)

    # Créer le graphique à barres côte à côte avec Plotly graph_objs
    fig_comparison = go.Figure()

    # Ajouter les barres pour 'M' (hommes)
    fig_comparison.add_trace(go.Bar(
        x=aggregated_monthly_data['Date'],
        y=aggregated_monthly_data['M'],
        name='Hommes',
        marker_color='blue'
    ))

    # Ajouter les barres pour 'F' (femmes)
    fig_comparison.add_trace(go.Bar(
        x=aggregated_monthly_data['Date'],
        y=aggregated_monthly_data['F'],
        name='Femmes',
        marker_color='pink'
    ))

    # Mise en page du titre et des étiquettes des axes
    fig_comparison.update_layout(
        title='Comparaison du nombre de bénéficiaires hommes et femmes par mois',
        xaxis_title='Mois',
        yaxis_title='Nombre de bénéficiaires',
        barmode='group'  # Pour afficher les barres côte à côte
    )

    # Afficher le graphique dans Streamlit
    st.plotly_chart(fig_comparison)

# Carte interactive des villages
#  st.markdown("### Carte Interactive des Villages")
# m = folium.Map(location=[15.0, -15.0], zoom_start=6)  # Initialiser la carte centrée sur le Sénégal

# # Ajouter des points pour chaque village
# for _, row in filtered_data.iterrows():
#     folium.Marker(
#         location=[row['latitude'], row['longitude']],
#         popup=f"Village: {row['Régions']}<br>Activité: {row['Activité']}<br>Total Bénéficiaires: {row['Total Beneficiaire']}",
#         icon=folium.Icon(color='blue', icon='info-sign')
#     ).add_to(m)

# # Afficher la carte dans Streamlit
# st_folium(m, width=700, height=500) 

# # Carte interactive des villages avec clustering
# st.markdown("### Carte Interactive des Villages")
# m = folium.Map(location=[15.0, -15.0], zoom_start=6)  # Initialiser la carte centrée sur le Sénégal
# marker_cluster = MarkerCluster().add_to(m)

# # Ajouter des points pour chaque village
# for _, row in filtered_data.iterrows():
#     folium.Marker(
#         location=[row['latitude'], row['longitude']],
#         popup=f"Village: {row['Régions']}<br>Activité: {row['Activité']}<br>Total Bénéficiaires: {row['Total Beneficiaire']}",
#         icon=folium.Icon(color='blue', icon='info-sign')
#     ).add_to(marker_cluster)

# # Afficher la carte dans Streamlit
# st_folium(m, width=700, height=500)
footer_html = """<div style='text-align: center;'>
  <p>Developed with ❤️ by 
<a href="https://www.linkedin.com/in/mouhamadou-tall/">Mouhamadou TALL</a>)</p>
</div>"""
st.markdown(footer_html, unsafe_allow_html=True)

hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)




##### test



import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import geopandas as gpd
import plotly.express as px
import plotly.graph_objs as go
from data_loader import load_data  # Assurez-vous que ce module est correct
from utils import merge_data, filter_data  # Assurez-vous que ce module est correct
from datetime import datetime

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
st.sidebar.markdown("""
Ce tableau de bord présente une analyse des activités avec un focus sur les bénéficiaires.

Contactez-nous pour plus d'informations :
- [CorpsAfrica/Sénégal](https://www.corpsafrica.org/where-we-work/senegal/)
- Téléphone : [+221 77 00 00 00](tel:+221770000000)
- Email : [QgqFP@example.com](mailto:QgqFP@example.com)
""")
# Filtres

with st.sidebar:
    st.title('Analyse des Activités')
    
    zone = st.sidebar.selectbox('Zone', options=[None] + list(data['ZONE'].unique()))
    sexe = st.sidebar.radio('Sexe', options=[None, 'M', 'F'], index=0, key='sexe_filter')
    age_group = st.sidebar.selectbox("Tranche d'âge", options=[None, '-18', '18-24', '25-35', '35+'], key='age_filter')
    activity_type = st.sidebar.selectbox('Type d\'activité', options=[None] + list(data['Activité'].unique()), key='activity_type_filter')
    # Sélection de la plage de dates avec un slider
    min_date = pd.Timestamp(data['Date'].min())
    max_date = pd.Timestamp(data['Date'].max())
    # Slider vertical pour la sélection de dates
    start_date, end_date = st.sidebar.slider('Sélectionner une plage de dates',
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
col1.metric("Villages", data['village_id'].nunique())
col2.metric("Communes", data['commune'].nunique())
col3.metric("Départements", data['département'].nunique())
col4.metric("Nombre de Régions", data['région'].nunique())

# Row 2: Maps and Charts
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Répartition des Volontaires au Sénégal")
    m = folium.Map(location=[14.4974, -14.4524], zoom_start=6)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in filtered_data.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"Village: {row['village']}<br>Activité: {row['activité']}<br>Total Bénéficiaires: {row['total_beneficiaires']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(marker_cluster)

    st_folium(m, width=700, height=500)

with col2:
    st.markdown("### Répartition des Volontaires par Sexe")
    pie_data = filtered_data['sexe'].value_counts().reset_index()
    pie_data.columns = ['Sexe', 'Total Beneficiaire']
    pie_data['Sexe'] = pie_data['Sexe'].apply(lambda x: 'Masculin' if x == 'M' else 'Féminin')
    fig_pie = px.pie(pie_data, values='Total Beneficiaire', names='Sexe', title='Répartition par Sexe')
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("### Répartition des Volontaires par Région")
    region_data = filtered_data.groupby('région')['total_beneficiaires'].sum().reset_index()
    fig_region = px.bar(region_data, x='région', y='total_beneficiaires', title='Répartition par Région')
    st.plotly_chart(fig_region, use_container_width=True)

# Row 3: Activity and Beneficiaries
col1, col2 = st.columns([1, 1])
col1.metric("Sections d'Activités", data['section_activite'].nunique())
col1.metric("Activités", data['activité'].nunique())
col2.metric("Bénéficiaires Directs", data['total_beneficiaires'].sum())
col2.metric("Bénéficiaires Indirects", data['beneficiaires_indirects'].sum())

# Row 4: Detailed Charts
st.markdown("### Total Bénéficiaires par Secteur d'Activité")
activity_sector = filtered_data.groupby('activité')['total_beneficiaires'].sum().reset_index()
fig_activity = px.bar(activity_sector, x='activité', y='total_beneficiaires', title='Total Bénéficiaires par Activité')
st.plotly_chart(fig_activity, use_container_width=True)

st.markdown("### Total Bénéficiaires par Mois")
filtered_data['month'] = filtered_data['date'].dt.to_period('M')
aggregated_monthly_data = filtered_data.groupby('month')['total_beneficiaires'].sum().reset_index()
aggregated_monthly_data['month'] = aggregated_monthly_data['month'].astype(str)
fig_monthly = px.line(aggregated_monthly_data, x='month', y='total_beneficiaires', title='Total Bénéficiaires par Mois')
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
