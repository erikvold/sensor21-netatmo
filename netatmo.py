
import requests
import json
import datetime
import time

config_data = {}
with open('config.json', 'r') as config:
     config_data = json.load(config)

try:
    response = requests.post("https://api.netatmo.com/oauth2/token", data={
        'grant_type': 'password',
        'username': config_data['username'],
        'password': config_data['password'],
        'client_id': config_data['client_id'],
        'client_secret': config_data['client_secret'],
        'scope': 'read_station'})
    response.raise_for_status()
    access_token=response.json()["access_token"]
    refresh_token=response.json()["refresh_token"]
    scope=response.json()["scope"]
    print("Your access token is retrieved.")
except requests.exceptions.HTTPError as error:
    print(error.response.status_code, error.response.text)

class Netatmo():
    def data():
        params = {
          'access_token': access_token,
          'device_id': config_data['device_id']
        }
        data = "{}"
        timestamp = ""
        barometer_package = []

        try:
            response = requests.post("https://api.netatmo.com/api/getstationsdata", params=params)
            response.raise_for_status()
            device = response.json()["body"]["devices"][0]
            time1 = device["dashboard_data"]["time_utc"]
            time2 = device["modules"][0]["dashboard_data"]["time_utc"]
            if time1 > time2:
                timestamp = time1
            else:
                timestamp = time2

            barometer_package.append({
                'timestamp': str(datetime.datetime.fromtimestamp(int(timestamp))),
                'temperature': device["modules"][0]["dashboard_data"]["Temperature"],
                'pressure': round(device["dashboard_data"]["Pressure"] * 100, 1),
            })

        except requests.exceptions.HTTPError as error:
            print(error.response.status_code, error.response.text)

        return barometer_package

    def lastupdate():
        params = {
          'access_token': access_token,
          'device_id': config_data['device_id']
        }
        diff = 500
        timestamp=""

        try:
            response = requests.post("https://api.netatmo.com/api/getstationsdata", params=params)
            response.raise_for_status()

            devices = response.json()["body"]["devices"][0]
            time1 = devices["dashboard_data"]["time_utc"]
            time2 = devices["modules"][0]["dashboard_data"]["time_utc"]

            if time1 > time2:
                timestamp = time1
            else:
                timestamp = time2

            diff = ((time.time() - timestamp))

        except requests.exceptions.HTTPError as error:
            print(error.response.status_code, error.response.text)

        return diff


if __name__ == '__main__':
    latest_measurement  = Netatmo
    data = latest_measurement.data()
    formatted_data = json.dumps(data, indent=2, sort_keys=True)
    print(formatted_data)
