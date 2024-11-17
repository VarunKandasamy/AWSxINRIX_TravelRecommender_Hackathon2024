import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Function to get the current temperature from WeatherAPI
def get_temperature(city):
    api_key = "a335bd2b726341bc9ef24526241711"  # Replace with your WeatherAPI key
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&aqi=no"  # "aqi=no" to exclude air quality data

    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        temperature = data.get('current', {}).get('temp_c', None)  # Get temperature in Celsius
        if temperature is not None:
            return f"The current temperature in {city} is {temperature}°C."
        else:
            return "Temperature data not found."
    else:
        return f"Error: {response.status_code}"

@app.route("/", methods=["GET", "POST"])
def index():
    city = ""
    temperature_info = ""
    
    if request.method == "POST":
        # Get city name from the form
        city = request.form["city"]
        # Call function to get temperature
        temperature_info = get_temperature(city)

    return render_template("index.html", city=city, temperature_info=temperature_info)

if __name__ == "__main__":
    app.run(debug=True)
