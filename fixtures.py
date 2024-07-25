import http.client
from config import API_KEY  # Import the API key

def fetch_fixtures():
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")

    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }

    conn.request("GET", "https://v3.football.api-sports.io/fixtures?team=85&season=2024&from=2024-01-01&to=2024-07-25", headers=headers)
    res = conn.getresponse()
    data = res.read()

    return data.decode("utf-8")
