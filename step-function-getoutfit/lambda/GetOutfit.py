import urllib.request
import urllib.parse
import json
import os

def suggest_outfit(temp_f, condition_text, wind_mph, snow_cm, is_sunny):
    # create criteria for snow and wind
    snow_warning = snow_cm > 0
    wind_strong = wind_mph >= 10

    if snow_warning:
        return "It's snowing — use thicker outfits and boots with proper grip for icy surfaces."

    outfit = ""

    # Determine the result for each description and temperature while also considering the strength of the wind
    if is_sunny and temp_f > 68:
        outfit = "A t-shirt and breathable pants or a skirt should be fine. Sunglasses are recommended."
    elif 50 < temp_f <= 68:
        outfit = "Wear a light sweater or jacket with jeans or pants."
        if wind_strong:
            outfit += " Since the wind is strong, consider a thicker jacket to stay warm."
    elif 41 <= temp_f <= 50:
        outfit = "Opt for a warm jacket or layered sweater with full-length pants."
        if wind_strong:
            outfit += " The wind might make it feel colder — wear a heavier coat or windbreaker."
    elif temp_f < 41:
        outfit = "You’ll need a warm coat, gloves, and boots."
        if wind_strong:
            outfit += " The wind makes it feel even colder — wear a much thicker coat, scarf, and thermal layers."

    if "rain" in condition_text.lower():
        outfit += " Don’t forget a waterproof layer or umbrella."
    elif "sun" in condition_text.lower():
        outfit += " Enjoy the sun, but bring sunglasses if you're sensitive to light."

    return outfit.strip()

# Try to get the weather for the cities from GetTimezone.py with dedicated time block
# Then send to getUserList.py
def lambda_handler(event, context):
    cities = event.get("cities", [])
    if not cities:
        return {"error": "No cities provided"}

    API_KEY = os.environ.get("weather_api_key")
    if not API_KEY:
        return {"error": "Missing weather API key in environment variables"}

    outfit_map = {}

    # get the list of cities from GetTimezone.py and get their weather.
    for city in cities:
        url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={urllib.parse.quote(city)}&days=1&aqi=no&alerts=no"

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
        except Exception as e:
            print(f"⚠️ Failed to fetch weather for {city}: {e}")
            continue

        forecast_hours = data.get("forecast", {}).get("forecastday", [])[0].get("hour", [])


        time_blocks = [
            (9, 18),   
            (9, 21),  
            (9, 12),  
            (12, 15),  
            (15, 18),  
            (18, 21)   
        ]

        city_outfits = {}

        for start_hour, end_hour in time_blocks:
            selected_hours = [
                hour for hour in forecast_hours
                if start_hour <= int(hour["time"].split()[1].split(":")[0]) < end_hour
            ]

            if not selected_hours:
                city_outfits[f"{start_hour}:00 - {end_hour}:00"] = "No data"
                continue

            # find average of the statistics for the day and put it into suggest_outfit param
            avg_temp = sum(h["temp_f"] for h in selected_hours) / len(selected_hours)
            avg_wind = sum(h["wind_mph"] for h in selected_hours) / len(selected_hours)
            total_snow = sum(h["snow_cm"] for h in selected_hours)
            common_condition = max(
                set(h["condition"]["text"] for h in selected_hours),
                key=lambda x: sum(h["condition"]["text"] == x for h in selected_hours)
            )
            is_sunny = "sun" in common_condition.lower()

            outfit = suggest_outfit(avg_temp, common_condition, avg_wind, total_snow, is_sunny)
            city_outfits[f"{start_hour}:00 - {end_hour}:00"] = outfit

        outfit_map[city] = city_outfits

    return {
        "cities": cities,
        "outfit_map": outfit_map
    }
