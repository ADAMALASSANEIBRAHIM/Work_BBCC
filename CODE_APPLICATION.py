import streamlit as st
import pandas as pd
import requests
import pydeck as pdk

# URL du fichier CSV sur GitHub
url = 'https://raw.githubusercontent.com/ADAMALASSANEIBRAHIM/Work_BBCC/main/CITIES_CEDEAO.csv'

# Charger les données des fichiers CSV locaux
file_path1 = 'https://raw.githubusercontent.com/ADAMALASSANEIBRAHIM/Work_BBCC/main/pays_CED.csv'  # Assurez-vous que le format est correct
cedeao_data = pd.read_csv(file_path1, encoding='ISO-8859-1', sep=';')

file_path2 = 'https://raw.githubusercontent.com/ADAMALASSANEIBRAHIM/Work_BBCC/main/pays_CED2.csv'  # Assurez-vous que le format est correct
prediction_data = pd.read_csv(file_path2, encoding='ISO-8859-1', sep=';')

nom = {'couleurs ': 'couleurs'}
prediction_data.rename(columns=nom, inplace=True)

# Charger les données du fichier CSV sur GitHub
cities = pd.read_csv(url, encoding='ISO-8859-1', sep=';')  # ou 'latin1'
# Remplacer les noms de colonnes pour qu'ils soient cohérents
new_column_names = {'villes ': 'villes', 'pays ': 'pays'}
cities.rename(columns=new_column_names, inplace=True)

API_KEY = '9bca7584ddf75ac402bf7cd3cb173813'

# Fonction pour obtenir les informations climatiques
def get_weather_data(city):
    if city in cities['villes'].values:
        city_info = cities[cities['villes'] == city].iloc[0]
        country = city_info['pays']
        URL = f'http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={API_KEY}&units=metric&lang=fr'
        response = requests.get(URL, verify=False)  # Désactiver la vérification du certificat SSL
        if response.status_code == 200:
            data = response.json()
            temperature = data['main']['temp']
            conditions_meteorologiques = data['weather'][0]['description']
            humidite = data['main']['humidity']
            vitesse_du_vent = data['wind']['speed']
            return {
                "Ville": city,
                "Pays": country,
                "Température": f"{temperature}°C",
                "Conditions météorologiques": conditions_meteorologiques,
                "Humidité": f"{humidite}%",
                "Vitesse du vent": f"{vitesse_du_vent} m/s"
            }
        else:
            return None
    else:
        return None

# Fonction pour obtenir les données météorologiques pour un DataFrame de villes
def get_weather_data_for_df(cities_df, api_key):
    villes_df = cities_df.copy()
    villes_df['Temperature'] = None
    villes_df['Humidity'] = None
    villes_df['Wind Speed'] = None
    villes_df['Conditions météorologiques'] = None
    for index, row in villes_df.iterrows():
        city_name = row['villes']
        weather_info = get_weather_data(city_name)
        if weather_info:
            villes_df.at[index, 'Temperature'] = weather_info['Température']
            villes_df.at[index, 'Humidity'] = weather_info['Humidité']
            villes_df.at[index, 'Wind Speed'] = weather_info['Vitesse du vent']
            villes_df.at[index, 'Conditions météorologiques'] = weather_info['Conditions météorologiques']
        else:
            villes_df.at[index, 'Temperature'] = 'Données non disponibles'
            villes_df.at[index, 'Humidity'] = 'Données non disponibles'
            villes_df.at[index, 'Wind Speed'] = 'Données non disponibles'
            villes_df.at[index, 'Conditions météorologiques'] = 'Données non disponibles'
    return villes_df

# Streamlit app
def main():
    st.title("Carte des Villes en Afrique de l'Ouest")

    # Sidebar filters
    country_filter = st.sidebar.multiselect('Sélectionnez le(s) pays', cities['pays'].unique())
    if country_filter:
        region_filter = st.sidebar.multiselect('Sélectionnez la/les région(s)', cities[cities['pays'].isin(country_filter)]['region'].unique())
    else:
        region_filter = st.sidebar.multiselect('Sélectionnez la/les région(s)', cities['region'].unique())

    if region_filter:
        city_filter = st.sidebar.multiselect('Sélectionnez la/les ville(s)', cities[cities['region'].isin(region_filter)]['villes'].unique())
    else:
        city_filter = st.sidebar.multiselect('Sélectionnez la/les ville(s)', cities['villes'].unique())

    # Apply filters
    filtered_cities = cities
    if country_filter:
        filtered_cities = filtered_cities[filtered_cities['pays'].isin(country_filter)]
    if region_filter:
        filtered_cities = filtered_cities[filtered_cities['region'].isin(region_filter)]
    if city_filter:
        filtered_cities = filtered_cities[filtered_cities['villes'].isin(city_filter)]

    # Afficher la carte détaillée avec pydeck
    deck_map = pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=filtered_cities['latitude'].mean(),
            longitude=filtered_cities['longitude'].mean(),
            zoom=5,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=filtered_cities,
                get_position='[longitude, latitude]',
                get_color='[200, 30, 0, 160]',
                get_radius=20000,
                pickable=True
            ),
        ],
        tooltip={"text": "{villes}"}
    )
    st.pydeck_chart(deck_map)

    # Gestionnaire de clics
    if 'deck_clicked' not in st.session_state:
        st.session_state['deck_clicked'] = None

    clicked_city = st.session_state.get("deck_clicked", None)
    if clicked_city:
        city_info = filtered_cities[filtered_cities['villes'] == clicked_city].iloc[0]
        weather_info = get_weather_data(city_info['villes'])
        if weather_info:
            st.write("### Informations Climatiques")
            st.write(f"**Ville**: {weather_info['Ville']}")
            st.write(f"**Région**: {city_info['region']}")
            st.write(f"**Pays**: {weather_info['Pays']}")
            st.write(f"**Température**: {weather_info['Température']}")
            st.write(f"**Humidité**: {weather_info['Humidité']}")
            st.write(f"**Vitesse du vent**: {weather_info['Vitesse du vent']}")
            st.write(f"**Conditions météorologiques**: {weather_info['Conditions météorologiques']}")
        else:
            st.write("Erreur: Impossible de récupérer les données climatiques.")

    # Ajouter une option pour afficher les données climatiques des villes filtrées
    if st.sidebar.checkbox('Afficher les données climatiques des villes filtrées'):
        weather_df = get_weather_data_for_df(filtered_cities, API_KEY)
        st.write("### Données Climatiques des Villes Filtrées")
        st.write(weather_df)

    # Mise à jour de l'état de la session pour le clic suivant
    def update_clicked_city(city):
        st.session_state['deck_clicked'] = city

    # Assurez-vous que le clic sur la carte met à jour l'état de la ville cliquée
    deck_map.tooltip = {
        "text": "{villes}",
        "on_click": update_clicked_city
    }

def prediction_analysis():
    st.title('Prédiction et Analyse')

    # Filtres pour la feuille 'prediction_data'
    country_filter = st.sidebar.multiselect('Sélectionnez le(s) pays', prediction_data['pays'].unique())

    # Apply filters
    filtered_prediction = prediction_data
    if country_filter:
        filtered_prediction = filtered_prediction[filtered_prediction['pays'].isin(country_filter)]

    # Vérifier si la colonne 'prediction' existe
    if 'prédiction' in filtered_prediction.columns:
        # Ajouter une colonne de prédiction
        # filtered_prediction['prédiction'] = filtered_prediction['prédiction']
        filtered_prediction['couleurs'] = filtered_prediction['prédiction'].apply(
            lambda x: [0, 255, 0, 160] if x == 'positive' else [255, 0, 0, 160]  # Vert pour prédiction positive, rouge pour négative
        )
            # Afficher la carte des prédictions
        deck_map_variation = pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=filtered_prediction['Latitude'].mean(),
                longitude=filtered_prediction['Longitude'].mean(),
                zoom=5,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=filtered_prediction,
                    get_position='[Longitude, Latitude]',
                    get_color='couleurs',  # Vert pour prédiction positive, rouge pour prédiction négative
                    get_radius=20000,
                    pickable=True
                ),
            ],
            tooltip={"text": "{pays}"}
        )
        st.pydeck_chart(deck_map_variation)
    else:
        st.error("La colonne 'prediction' n'existe pas dans les données de prédiction.")

if __name__ == '__main__':
    st.sidebar.title('Menu')
    menu = st.sidebar.radio("Sélectionnez une option", ["Carte des Villes en Afrique de l'Ouest", 'Prédiction et Analyse'])

    if menu == "Carte des Villes en Afrique de l'Ouest":
        main()
    elif menu == 'Prédiction et Analyse':
        prediction_analysis()


#Ateention: POUR EXECUTER L'APPLICATION IL FAUT EXEXUCTER COMME:
     # PS C:\Users\SAMSON> cd C:\Users\SAMSON\Downloads
    #PS C:\Users\SAMSON\Downloads> streamlit run vscode3.py