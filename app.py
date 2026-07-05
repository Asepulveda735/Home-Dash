from flask import Flask, jsonify
from dotenv import load_dotenv
import requests
import os



# Load environment variables from .env
load_dotenv()

OWM_API_KEY = os.getenv("OWM_API_KEY")
CTA_API_KEY = os.getenv("CTA_API_KEY")  # or whatever transit key you got



app = Flask(__name__)

from flask import render_template

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/")
def home():
    return "Dashboard backend is running."


@app.route("/api/weather")
def get_weather():
    # TODO:
    params = {
        "q": "Wheeling,IL,US",
        "appid": OWM_API_KEY,
        "units": "imperial"
}
    response = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    response_json = response.json()
    return jsonify(response_json)


    # 1. Build the request URL using OWM_API_KEY and a city (e.g. "Wheeling,IL,US")
    # 2. Call it with requests.get()
    # 3. Convert the response to JSON with .json()
    # 4. Return it using jsonify()
    pass


@app.route("/api/transit")
def get_transit():
    # TODO:
    params = {
        "key": CTA_API_KEY,
        "mapid": "41220",#fullerton stop ID
        "outputType": "JSON"
}
    response = requests.get("http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx", params=params)
    response_json = response.json()
    return jsonify(response_json)


    # 1. Build the request URL using CTA_API_KEY and a stop/route ID
    # 2. Call it with requests.get()
    # 3. Convert the response to JSON with .json()
    # 4. Return it using jsonify()
    pass


if __name__ == "__main__":
    app.run(debug=True)