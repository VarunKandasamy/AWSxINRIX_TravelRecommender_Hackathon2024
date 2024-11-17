import requests
import boto3
import json
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

# Set up AWS Bedrock client
bedrock_client = boto3.client('bedrock', region_name='us-west-2')  # Replace with your region

# Function to query Bedrock for nearby cities within the specified radius
def get_nearby_cities(city, radius_miles):
    #prompt = f"Please list cities that are within {radius_miles} miles of {city}."
    prompt = "List five cities in California.";

    try:
        # Make request to Bedrock
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',  # Replace with your actual Bedrock model ID
            body=json.dumps({
                "prompt": prompt,
                "max_tokens": 150
            })
        )

        # Process the response
        response_body = response['body'].read().decode('utf-8')
        response_json = json.loads(response_body)
        print(json.dumps(response_json, indent=4))  # Pretty print JSON with indentation
        nearby_cities = response_json.get('choices', [{}])[0].get('text', '').strip()

        if nearby_cities:
            return nearby_cities.split('\n')  # Assume the response is a newline-separated list of cities
        else:
            return []

    except Exception as e:
        print(f"Error querying Bedrock: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    city = ""
    temperature_info = ""
    nearby_cities = []
    
    if request.method == "POST":
        # Get city name from the form
        city = request.form["city"]
        # Call function to get temperature
        temperature_info = get_temperature(city)
        
        # Get the radius from the form (default to 5 miles if not provided)
        radius_miles = int(request.form.get("radius", 5))
        
        # Query Bedrock for nearby cities
        nearby_cities = get_nearby_cities(city, radius_miles)

    return render_template("index.html", city=city, temperature_info=temperature_info, nearby_cities=nearby_cities)

if __name__ == "__main__":
    app.run(debug=True)
