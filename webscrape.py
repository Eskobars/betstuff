from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import random
from datetime import datetime
import pandas as pd

# Initialize the browser
driver = webdriver.Firefox()
driver.get('https://nr.soccerway.com/')
time.sleep(random.uniform(0.5, 1.0))  # Random sleep between 0.5 and 1.0 seconds

# Reject cookies
try:
    driver.find_element(By.CSS_SELECTOR, "button[id='onetrust-reject-all-handler']").click()
    time.sleep(random.uniform(0.5, 1.0))  # Random sleep between 0.5 and 1.0 secondsc

except NoSuchElementException:
        print(f"Cookies already allowed. Skipping.")
        
# Define leagues to navigate to
# leagues = [
#     'English Premier League',
#     'Kansallinen Liiga',
#     'La Liga',
#     'Serie A',
#     'Bundesliga',
#     'Ligue 1',
#     'Eredivisie',
#     'Primeira Liga',
#     'Scottish Premiership',
#     'Brasileirão Serie A',
#     'Argentine Primera División',
#     'Major League Soccer',
#     'J1 League',
#     'K League 1',
#     'Qatar Stars League',
#     'Saudi Pro League',
#     'Egyptian Premier League',
#     'South African Premier Division',
#     'A-League'
# ]

leagues = [
    'Kansallinen Liiga',
    'Liga Profesional Argentina',
    'Primera Nacional',
    '1. Division',
    'Serie B',
    'Primera B',
    'Segunda División',
    'Tercera A',
    'Primera A',
    'Kakkonen'
] #Test set 1

# Define time range for filtering matches
current_date = pd.Timestamp.now()
epoch_time = datetime(1970, 1, 1)
delta = (current_date - epoch_time)
delta_seconds = int(delta.total_seconds())

one_day_epoch = 86400
min_time = delta_seconds - one_day_epoch
max_time = delta_seconds + one_day_epoch

# Lists to store games based on star rating
one_star_games = []
two_star_games = []
three_star_games = []

for league in leagues:
    try:
        # Attempt to find and click on the league link
        league_link = driver.find_element(By.PARTIAL_LINK_TEXT, league)
        league_link.click()
        time.sleep(random.uniform(0.5, 1.0))  # Random sleep between 0.5 and 1.0 seconds

        # Retrieve team rankings
        team_element_list = driver.find_elements(By.XPATH, "//table[contains(@class,'leaguetable sortable table detailed-table')]/tbody/tr")
        
        num_teams = len(team_element_list)
        if num_teams == 0:
            continue  # Skip if no teams are found

        # Initialize variables
        team_rankings = {}
        
        # Extract team rankings and details
        for team in team_element_list:
            team_info = team.text.split()
            numeric_indices = [i for i, item in enumerate(team_info) if item.isdigit()]
            rank = int(team_info[0])
            split_index = numeric_indices[1]
            team_name = ' '.join(team_info[1:split_index])
            team_rankings[team_name] = rank

        # Calculate bottom 33% threshold
        worst_team_element = team_element_list[-1]
        worst_team_info = worst_team_element.text.split()
        worst_team_rank = int(worst_team_info[0])
        bottom_33_threshold = worst_team_rank - (num_teams // 3)

        element_list = driver.find_elements(By.XPATH, "//table[contains(@class,'matches')]/tbody/tr")
        for item in element_list:
            item_text = item.text

            # Skip games with "FT" (already played)
            if 'FT' in item_text:
                continue

            timestamp_attribute = item.get_attribute('data-timestamp')
            if min_time <= int(timestamp_attribute) <= max_time:
                # Skip if the game is on a specific day of the week
                if any(day in item_text for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                    continue
                
                # Extract names of teams playing
                team_names = item_text.split('\n')
                home_team = team_names[1]
                away_team = team_names[3]

                # Initialize ranks and other values for comparison
                home_team_rank = None
                away_team_rank = None
                home_team_goal_difference = 0  # Default value
                away_team_goal_difference = 0  # Default value
                home_team_game_record = []  # Ensure this is initialized
                away_team_game_record = []  # Ensure this is initialized
                warnings = []  # Use a list to accumulate warnings

                # Check stats for teams
                for team_name, rank in team_rankings.items():
                    if team_name == home_team:
                        home_team_rank = rank
                    elif team_name == away_team:
                        away_team_rank = rank

                # Ensure ranks are available before proceeding
                if home_team_rank is not None and away_team_rank is not None:
                    # Check if both teams are in the bottom 33% of the league
                    if home_team_rank >= bottom_33_threshold and away_team_rank >= bottom_33_threshold:
                        warnings.append("Both teams are in the bottom 33% of the league")
                    
                    # Calculate stats
                    placement_difference = abs(home_team_rank - away_team_rank)
                    if placement_difference > 10:
                        placement_points_home = 2 if home_team_rank < away_team_rank else 0
                        placement_points_away = 2 if away_team_rank < home_team_rank else 0
                    elif 5 < placement_difference <= 10:
                        placement_points_home = 1 if home_team_rank < away_team_rank else 0
                        placement_points_away = 1 if away_team_rank < home_team_rank else 0
                    else:
                        placement_points_home = 0
                        placement_points_away = 0

                    # Ensure goal difference values are properly handled
                    if home_team_goal_difference is None:
                        home_team_goal_difference = 0
                    if away_team_goal_difference is None:
                        away_team_goal_difference = 0

                    # Calculate goal points for home team
                    if home_team_goal_difference > 15:
                        home_goal_points = 2
                    elif 0 < home_team_goal_difference <= 15:
                        home_goal_points = 1
                    elif -15 < home_team_goal_difference <= 0:
                        home_goal_points = -1
                    else:
                        home_goal_points = -2

                    # Calculate goal points for away team
                    if away_team_goal_difference > 15:
                        away_goal_points = 2
                    elif 0 < away_team_goal_difference <= 15:
                        away_goal_points = 1
                    elif -15 < away_team_goal_difference <= 0:
                        away_goal_points = -1
                    else:
                        away_goal_points = -2

                    # Calculate recent performance points for home team
                    if home_team_game_record[-5:] == ['W', 'W', 'W', 'W', 'W']:
                        home_recent_performance_points = 2
                    elif home_team_game_record[-5:] == ['L', 'L', 'L', 'L', 'L']:
                        home_recent_performance_points = -2
                    elif home_team_game_record[-3:] == ['W', 'W', 'W']:
                        home_recent_performance_points = 1
                    elif home_team_game_record[-3:] == ['L', 'L', 'L']:
                        home_recent_performance_points = -1
                    else:
                        home_recent_performance_points = 0

                    # Calculate recent performance points for away team
                    if away_team_game_record[-5:] == ['W', 'W', 'W', 'W', 'W']:
                        away_recent_performance_points = 2
                    elif away_team_game_record[-5:] == ['L', 'L', 'L', 'L', 'L']:
                        away_recent_performance_points = -2
                    elif away_team_game_record[-3:] == ['W', 'W', 'W']:
                        away_recent_performance_points = 1
                    elif away_team_game_record[-3:] == ['L', 'L', 'L']:
                        away_recent_performance_points = -1
                    else:
                        away_recent_performance_points = 0

                    # Check if season has just started
                    matches_played_threshold = 10  # Adjust based on typical early-season number of matches
                    if any([team_rankings[home_team] <= matches_played_threshold, team_rankings[away_team] <= matches_played_threshold]):
                        warnings.append("The season just started.")

                    # Additional points condition
                    additional_points_home = 1
                    additional_points_away = -1

                    total_points_home = placement_points_home + home_goal_points + home_recent_performance_points + additional_points_home
                    total_points_away = placement_points_away + away_goal_points + away_recent_performance_points + additional_points_away

                    # Determine the point difference and star rating
                    point_difference = abs(total_points_home - total_points_away)
                    if point_difference <= 2:
                        bet_rank = 1
                    elif point_difference <= 4:
                        bet_rank = 2
                    elif point_difference <= 6:
                        bet_rank = 3
                    else:
                        bet_rank = 0

                    # Determine winner
                    winner = ""
                    if total_points_home > total_points_away:
                        if total_points_away < 0:
                            if point_difference >= 2:
                                winner = home_team
                        else:
                            if point_difference >= 2:
                                winner = home_team

                    elif total_points_away > total_points_home:
                        if total_points_home < 0:
                            if point_difference >= 2:
                                winner = away_team
                        else:
                            if point_difference >= 2:
                                winner = away_team

                    if winner:
                        combined_warning = " | ".join(warnings) if warnings else " "
                        game_info = {
                            'Game Time': team_names[0],  # Assuming the time is the first item in team_names
                            'Home Team': home_team,
                            'Away Team': away_team,
                            'Predicted Winner': winner,
                            'Points Home': total_points_home,
                            'Points Away': total_points_away,
                            'Bet Rank': bet_rank,
                            'Warning': combined_warning
                        }
                        if bet_rank == 1:
                            one_star_games.append(game_info)
                        elif bet_rank == 2:
                            two_star_games.append(game_info)
                        elif bet_rank == 3:
                            three_star_games.append(game_info)

                    print(winner)

            time.sleep(random.uniform(0.5, 1.0))

        # Go back to the main page
        driver.execute_script("window.history.go(-1)")
        time.sleep(random.uniform(0.5, 1.0))

    except NoSuchElementException:
        print(f"League '{league}' not found. Skipping.")
        continue

# Close the browser
driver.quit()

# Print the collected games by star rating
print("1 Star Games:")
for game in one_star_games:
    print(f"{game['Warning']} {game['Home Team']} vs {game['Away Team']}, Predicted Winner: {game['Predicted Winner']}, Points Home: {game['Points Home']}, Points Away: {game['Points Away']}")

print("\n2 Star Games:")
for game in two_star_games:
    print(f"{game['Warning']} {game['Game Time']}: {game['Home Team']} vs {game['Away Team']}, Predicted Winner: {game['Predicted Winner']}, Points Home: {game['Points Home']}, Points Away: {game['Points Away']}")

print("\n3 Star Games:")
for game in three_star_games:
    print(f"{game['Warning']} {game['Game Time']}: {game['Home Team']} vs {game['Away Team']}, Predicted Winner: {game['Predicted Winner']}, Points Home: {game['Points Home']}, Points Away: {game['Points Away']}")
