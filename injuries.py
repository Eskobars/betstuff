import requests
from config import API_KEY  # Import the API key

# Function to fetch injury data from API-Football
def get_injury_data(team_id, season):
    BASE_URL = 'https://v3.football.api-sports.io/'
    
    headers = {
        'x-apisports-key': API_KEY
    }
    
    url = f'{BASE_URL}injuries?team={team_id}&season={season}'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error: {response.status_code}, {response.text}')
        return None