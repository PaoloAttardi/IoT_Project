import datetime
import holidays
import pandas as pd
import requests
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_percentage_error
import pickle

def predictorTraining():
    df = pd.read_csv("hour.csv")

    # Selezionare le feature rilevanti per la previsione
    relevant_features = ["season", "yr", "mnth", "hr", "holiday", "weekday", "workingday", "weathersit", "temp", "atemp", "hum"]

    # Applicare la trasformazione StandardScaler alle feature selezionate
    scaler = StandardScaler()
    X = scaler.fit_transform(df[relevant_features].values)

    # Separare la variabile dipendente dalla variabile predittiva
    y = df["cnt"].values.reshape(-1, 1)

    # Creare l'oggetto regressione lineare e addestrare il modello
    regressor = LinearRegression()
    regressor.fit(X, y)

    # Salvare il modello addestrato con pickle
    with open("regressor.pickle", "wb") as f:
        pickle.dump(regressor, f)

    # Valutare l'accuratezza del modello con la metrica MAPE
    y_pred = regressor.predict(X)
    mape = mean_absolute_percentage_error(y, y_pred)
    print(f"MAPE: {mape:.2f}")

    # Prevedere il numero di biciclette ora per ora per le prossime 24 ore
    last_hour = df.iloc[-1]["instant"]
    for i in range(24):
        hour = last_hour + i + 1
        data = scaler.transform(df[relevant_features].tail(1).values)
        data[0][3] = hour % 24  # Trasformare l'ora in un valore compreso tra 0 e 23
        prediction = int(regressor.predict(data))
        print(f"Ora {i}: {prediction} biciclette")

def newPrediction(lat, lon, now, ora):
    # lat e lon di default sono quelle di MODENA
    with open('regressor.pickle', 'rb') as f:
        regressor = pickle.load(f)

        # Ottieni le condizioni meteorologiche correnti da un API meteo
        api_key = '7709f02753c2a737ab142230c07b181d'
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}'
        response = requests.get(url)
        weather_data = response.json()
        # Ottieni la stagione in base al mese corrente
        if 3 <= now.month <= 5:
            season = 1  # Spring
        elif 6 <= now.month <= 8:
            season = 2  # Summer
        elif 9 <= now.month <= 11:
            season = 3  # Fall
        else:
            season = 4  # Winter
        yr = now.year - 2011  # 0 per il 2011, 1 per il 2012
        mnth = now.month
        # Crea un oggetto "Italy" che rappresenta le festività italiane
        it_holidays = holidays.IT()

        # Verifica se oggi è festività in Italia
        if datetime.date(now.year, now.month, now.day) in it_holidays:
            holiday = 1
        else:
            holiday = 0
        weekday = now.weekday()
        # Verifica se oggi è un giorno lavorativo
        if weekday < 5:  # 5 corrisponde a sabato, 6 a domenica
            workingday = 0
        else:
            workingday = 1
        # Ottieni il codice weathersit dalle condizioni meteorologiche
        if weather_data['weather'][0]['main'] in ['Clear','Few clouds','Partly cloudy']:
            weathersit = 1 
        elif weather_data['weather'][0]['main'] in ['Cloudy','Mist + Broken clouds','Few clouds','Mist']:
            weathersit = 2
        elif weather_data['weather'][0]['main'] in ['Light Snow','Light Rain']:
            weathersit = 3
        else:
            weathersit = 4
        temp = weather_data['main']['temp'] - 273.15  # Converti da Kelvin a Celsius
        atemp = weather_data['main']['feels_like'] - 273.15  # Converti da Kelvin a Celsius
        hum = weather_data['main']['humidity']

        # Effettua la predizione utilizzando il modello e i dati di input
        predizione = regressor.predict([[season, yr, mnth, ora, holiday, weekday, workingday, weathersit, temp, atemp, hum]])
        return predizione
    
def BucketList(config, client):
    query = f'from(bucket:"{config.get("InfluxDBClient","Bucket")}") |> range(start: -120h)'
    tables = client.query_api().query(query)

    # Select all the existing bowls
    table = {}
    for tab in tables:
      for row in tab.records:
        val = row.values["_field"]
        zone = row.values["_measurement"]
        if val not in table: table[val] = zone
    return table

import requests

def get_weather_forecast(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data["cod"] == "200":
        forecast = {}
        for forecast_data in data["list"]:
            date = forecast_data["dt_txt"].split()[0]  # Extracting date
            temperature = forecast_data["main"]["temp"]  # Extracting temperature
            if date in forecast:
                if forecast[date] >= temperature:
                    forecast[date] = temperature
            else:
                forecast[date] = temperature
        return forecast
    else:
        print("Error:", data["message"])
        return None