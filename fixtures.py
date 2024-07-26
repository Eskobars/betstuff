import http.client
from datetime import datetime
import json
from config import API_KEY  # Import the API key

def fetch_fixtures_for_day():
    try:
        # Get the current date
        today = datetime.today()
        # Format the date as YYYY-MM-DD
        current_date = today.strftime('%Y-%m-%d')

        conn = http.client.HTTPSConnection("v3.football.api-sports.io")

        headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': API_KEY
        }

        # Create the request URL for fixtures of the current day
        url = f"/fixtures?date={current_date}"
        conn.request("GET", url, headers=headers)

        res = conn.getresponse()
        data = res.read()

        # Check the response status
        if res.status != 200:
            print(f"Error fetching fixtures: {res.status} - {res.reason}")
            return None

        # Decode the JSON data
        parsed_data = json.loads(data.decode("utf-8"))

        # Check for the expected structure in the data
        if not parsed_data or 'response' not in parsed_data:
            print("No response field found in the data.")
            return None

        return parsed_data

    except Exception as e:
        print(f"An error occurred while fetching fixtures: {e}")
        return None

def get_fixtures_for_team(all_fixtures, team_name_fragment):
    if not all_fixtures or 'response' not in all_fixtures:
        print("Invalid fixtures data provided.")
        return []

    try:
        # Filter fixtures for the specific team name fragment
        team_fixtures = []
        for fixture in all_fixtures.get('response', []):
            home_team_name = fixture['teams']['home']['name'].lower()
            away_team_name = fixture['teams']['away']['name'].lower()

            if team_name_fragment.lower() in home_team_name or team_name_fragment.lower() in away_team_name:
                team_fixtures.append(fixture)

        if not team_fixtures:
            print(f"No fixtures found for team fragment: {team_name_fragment}")

        return team_fixtures

    except KeyError as e:
        print(f"KeyError: Missing expected key {e} in fixture data.")
        return []
    except Exception as e:
        print(f"An error occurred while filtering fixtures: {e}")
        return []
