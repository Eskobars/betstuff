import http.client
import json
from config import API_KEY

def fetch_players_for_fixture(fixture_id):
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")

    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }

    url = f"/fixtures/players?fixture={fixture_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    
    # Decode the JSON data
    parsed_data = json.loads(data.decode("utf-8"))
    
    return parsed_data

def get_key_players(player_data, rating_threshold=7.0):
    key_players = []

    # Traverse the response structure to access player statistics
    for team in player_data.get('response', []):
        for player in team.get('players', []):
            player_id = player['player']['id']
            player_name = player['player']['name']
            # Assuming rating is the first element in statistics list
            player_rating = float(player['statistics'][0]['games']['rating']) if 'rating' in player['statistics'][0]['games'] else 0.0
            
            if player_rating >= rating_threshold:
                key_players.append({
                    'id': player_id,
                    'name': player_name,
                    'rating': player_rating
                })

    return key_players
