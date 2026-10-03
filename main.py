import json
import os
from datetime import datetime
import requests

API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
HISTORY_FILE = "search_history.json"


# --- Pure Helper & Formatting Functions ---

def normalize_city_name(city_input: str) -> str:
    """Normalize input string by stripping whitespace and title-casing."""
    if not city_input:
        return ""
    return " ".join(city_input.strip().split()).title()


def format_weather_report(city: str, temperature: float, temp_unit: str, 
                          wind_speed: float, wind_unit: str, obs_time: str) -> str:
    """Format weather metrics into a clean visual report."""
    border = "+" + "-" * 42 + "+"
    lines = [
        border,
        f"| Weather Report: {city:<24} |",
        border,
        f"| Observation Time : {obs_time:<20} |",
        f"| Temperature      : {f'{temperature} {temp_unit}':<20} |",
        f"| Wind Speed       : {f'{wind_speed} {wind_unit}':<20} |",
        border
    ]
    return "\n".join(lines)


def format_history_list(history: list) -> str:
    """Format history list into a compact readable table."""
    if not history:
        return "No recent searches found."
    
    headers = f"{'#':<3} | {'Timestamp':<19} | {'City':<15} | {'Temp':<10}"
    divider = "-" * len(headers)
    output = [headers, divider]
    
    for idx, entry in enumerate(history, 1):
        temp_str = f"{entry.get('temperature')} {entry.get('temp_unit')}"
        output.append(f"{idx:<3} | {entry.get('timestamp'):<19} | {entry.get('city'):<15} | {temp_str:<10}")
        
    return "\n".join(output)


# --- Storage Functions ---

def load_history(filepath: str = HISTORY_FILE) -> list:
    """Load search history from a local JSON file."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_search_history(city: str, temperature: float, temp_unit: str, filepath: str = HISTORY_FILE) -> None:
    """Save successful lookup details to JSON history."""
    history = load_history(filepath)
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "city": city,
        "temperature": temperature,
        "temp_unit": temp_unit
    }
    history.insert(0, entry)  # Place recent search first
    history = history[:20]     # Retain latest 20 items
    
    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=2)
    except OSError as err:
        print(f"Warning: Failed to record search history: {err}")


# --- API Fetching Functions ---

def geocode_city(city_name: str) -> tuple:
    """Fetch coordinates for a given city name."""
    try:
        response = requests.get(GEOCODING_URL, params={"name": city_name, "count": 1}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results")
        if not results:
            return None, None, None
            
        first_result = results[0]
        resolved_name = f"{first_result['name']}, {first_result.get('country_code', '').upper()}"
        return resolved_name, first_result["latitude"], first_result["longitude"]
    except requests.RequestException as error:
        print(f"\n[Network Error] Geocoding request failed: {error}")
        return None, None, None


def get_weather(city: str, unit_system: str = "celsius") -> None:
    """Fetch and display weather data for a specified city."""
    resolved_city, lat, lon = geocode_city(city)
    if not lat or not lon:
        print(f"\nCould not find coordinates for city '{city}'. Please verify the spelling.")
        return

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "timezone": "auto"
    }
    
    if unit_system == "fahrenheit":
        params["temperature_unit"] = "fahrenheit"
        params["wind_speed_unit"] = "mph"

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        
        current = payload["current"]
        units = payload.get("current_units", {})
        
        temperature = current["temperature_2m"]
        wind_speed = current["wind_speed_10m"]
        obs_time = current.get("time", "N/A").replace("T", " ")
        
        temp_unit = units.get("temperature_2m", "°C" if unit_system == "celsius" else "°F")
        wind_unit = units.get("wind_speed_10m", "km/h" if unit_system == "celsius" else "mph")
        
        report = format_weather_report(resolved_city, temperature, temp_unit, wind_speed, wind_unit, obs_time)
        print(f"\n{report}\n")
        
        save_search_history(resolved_city, temperature, temp_unit)

    except requests.RequestException as error:
        print(f"\n[Network Error] Could not contact the weather service: {error}")
    except (ValueError, KeyError, TypeError) as error:
        print(f"\n[Data Error] Unexpected weather service response: {error}")


# --- Tests (Offline Execution) ---

def run_pure_tests():
    """Run unit tests on pure formatting and normalization functions."""
    assert normalize_city_name("  tbilisi  ") == "Tbilisi"
    assert normalize_city_name("NEW   YORK") == "New York"
    assert normalize_city_name("") == ""
    
    formatted = format_weather_report("Tbilisi", 22.5, "°C", 12.0, "km/h", "2026-10-03 09:00")
    assert "Tbilisi" in formatted
    assert "22.5 °C" in formatted
    
    mock_history = [{"timestamp": "2026-10-03 09:00", "city": "Tbilisi", "temperature": 22.5, "temp_unit": "°C"}]
    history_out = format_history_list(mock_history)
    assert "Tbilisi" in history_out
    
    print("All pure function unit tests passed successfully!")


# --- Interactive CLI Interface ---

def main():
    run_pure_tests()  # Run assertion checks on startup
    unit_preference = "celsius"
    
    while True:
        print("=== Open-Meteo Weather CLI ===")
        print("1. Search City Weather")
        print("2. View Search History")
        print(f"3. Change Units (Current: {unit_preference.capitalize()})")
        print("4. Exit")
        
        choice = input("Select an option (1-4): ").strip()
        
        if choice == "1":
            raw_city = input("Enter city name: ")
            city = normalize_city_name(raw_city)
            if not city:
                print("\n[Input Validation Error] City name cannot be empty.\n")
                continue
            get_weather(city, unit_preference)
            
        elif choice == "2":
            history = load_history()
            print(f"\n{format_history_list(history)}\n")
            
        elif choice == "3":
            print("\nSelect Unit:")
            print("1. Celsius (°C, km/h)")
            print("2. Fahrenheit (°F, mph)")
            unit_choice = input("Choice (1-2): ").strip()
            if unit_choice == "1":
                unit_preference = "celsius"
                print("\nUnit updated to Celsius.\n")
            elif unit_choice == "2":
                unit_preference = "fahrenheit"
                print("\nUnit updated to Fahrenheit.\n")
            else:
                print("\nInvalid choice. Keeping default unit.\n")
                
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("\n[Input Validation Error] Invalid menu choice. Enter a number between 1 and 4.\n")


if __name__ == "__main__":
    main()