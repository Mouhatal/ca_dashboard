import pandas as pd

def merge_data(villages, activities):
    try:
        # Vérifier les colonnes nécessaires pour la fusion
        if 'ZONE' in villages.columns and 'ZONE' in activities.columns:
            # Fusionner les DataFrames sur la colonne 'ZONE'
            merged_data = pd.merge(activities, villages, on='ZONE')
            return merged_data
        else:
            raise KeyError("Colonnes pour la fusion non trouvées dans les DataFrames.")
    
    except KeyError as e:
        raise KeyError(f"Erreur de fusion : {e}")
    except Exception as e:
        raise Exception(f"Erreur inattendue de fusion : {e}")

def filter_data(df, zone=None, region=None, sexe=None, age_group=None, activity_type=None, start_date=None, end_date=None):
    if zone:
        df = df[df['ZONE'] == zone]
    if sexe:
        if sexe == 'M':
            df = df[df[['M']].sum(axis=1) > 0]
        elif sexe == 'F':
            df = df[df[['F']].sum(axis=1) > 0]
    if age_group:
        if age_group == '-18':
            df = df[df[['-18|HOMME', '-18|FEMME']].sum(axis=1) > 0]
        elif age_group == '18-24':
            df = df[df[['18-24|HOMME', '18-24|FEMME']].sum(axis=1) > 0]
        elif age_group == '25-35':
            df = df[df[['25-35|HOMME', '25-35|FEMME']].sum(axis=1) > 0]
        elif age_group == '35+':
            df = df[df[['35|HOMME', '35|FEMME']].sum(axis=1) > 0]
    if activity_type:
        df = df[df['Activité'] == activity_type]
    if start_date:
        start_date = pd.Timestamp(start_date)
        df = df[pd.to_datetime(df['Date']) >= start_date]
    if end_date:
        end_date = pd.Timestamp(end_date)
        df = df[pd.to_datetime(df['Date']) <= end_date]
    return df
def calculate_totals(df, columns):
    return df[columns].sum()

def calculate_percentages(df, columns):
    totals = calculate_totals(df, columns)
    total_sum = totals.sum()
    return (totals / total_sum) * 100
