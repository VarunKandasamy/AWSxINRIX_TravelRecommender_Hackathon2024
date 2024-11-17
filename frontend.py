import requests
import boto3
import json
from flask import Flask, render_template, request
from functools import lru_cache
import os
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

# Configure request session with retry strategy and connection pooling
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Cache weather data for 5 minutes
@lru_cache(maxsize=100)
def get_cached_temperature(city, timestamp):
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

# Initialize Bedrock runtime client

def get_nearby_cities(city, radius_miles):
    if not (0 < radius_miles <= 100):  # Add reasonable limits
        return ["Invalid radius. Please enter a value between 1 and 100 miles."]

    #system_prompt = 'All your output should be is a list of cities'
    user_prompt = f"Please list cities that are within {radius_miles} miles of {city}"
    #prompt = f"System: {system_prompt}\n\nHuman: {user_prompt}\n\nAssistant:"
    modelId='anthropic.claude-3-haiku-20240307-v1:0'

    client = boto3.client(service_name="bedrock-runtime", region_name="us-west-2")

    try:
        response = client.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "system": "your output should be ONLY cities seperated by commas with NO WHITESPACES",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_prompt
                                }
                            ]
                        }
                    ],
                }
            ),
        )

        print(radius_miles)
        response_body = json.loads(response['body'].read().decode('utf-8'))
        print(response_body)
        model_output = response_body.get('text', '').strip()
        print('\n')
        print('\n')
        print('\n')
        print('\n')
        print('\n')
        print(model_output)
        print(response_body['content'][0]['text'])
        print('\n')
        city_string = response_body['content'][0]['text']
        nearby_cities = city_string.split(',')  
        return nearby_cities

    except Exception as e:
        print(f"Error querying Bedrock: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    city = ""
    temperature_info = ""
    nearby_cities = []
    
    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            return render_template("index.html", error="Please enter a city name")

        # Use current timestamp rounded to 5-minute intervals for caching
        timestamp = datetime.now().replace(second=0, microsecond=0)
        timestamp = timestamp - timedelta(minutes=timestamp.minute % 5)
        
        temperature_info = get_cached_temperature(city, timestamp)
        
        try:
            radius_miles = int(request.form.get("radius", 5))
            nearby_cities = get_nearby_cities(city, radius_miles)
        except ValueError:
            nearby_cities = ["Invalid radius value"]

    return render_template("index.html", 
                         city=city, 
                         temperature_info=temperature_info, 
                         nearby_cities=nearby_cities)

if __name__ == "__main__":
    app.run(debug=True)
