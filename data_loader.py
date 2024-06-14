import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    try:
        villages = pd.read_excel('data/map.xlsx')
        
        # Spécifiez le format des dates pour Pandas
        activities = pd.read_excel('data/activities.xlsx', parse_dates=['Date'], date_parser=lambda x: pd.to_datetime(x, format='%b. %Y'))

        # Optionnel : supprimez les lignes avec des dates invalides (NaN)
        activities = activities.dropna(subset=['Date'])

        # Formatage de la date comme souhaité
        activities['formatted_date'] = activities['Date'].dt.strftime('%b. %Y')

        return villages, activities
    except Exception as e:
        st.error(f"Erreur de chargement des données : {e}")
        return None, None
