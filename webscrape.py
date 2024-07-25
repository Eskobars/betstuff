from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from datetime import datetime
import pandas as pd
import json

# Import the custom module for API interactions
from injuries import get_injury_data
from fixtures import fetch_fixtures

def setup_driver():
    # Setup Firefox options
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")  # Comment this line if you want to see the browser UI

    # Setup Firefox driver
    driver = webdriver.Firefox(options=options)

    return driver

def main():
    driver = setup_driver()
    try:
        # Load the page
        driver.get('https://nr.soccerway.com/')
        
        # Set up explicit wait
        wait = WebDriverWait(driver, 10)  # Adjust timeout as necessary
        
        # Reject cookies if the button is present
        try:
            cookie_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-reject-all-handler']")))
            cookie_link.click()
            time.sleep(random.uniform(0.5, 1.0))  # Random sleep between 0.5 and 1.0 seconds
        except NoSuchElementException:
            print("Cookies already allowed or button not found. Skipping.")
        except TimeoutException:
            print("Timeout while trying to find the cookie rejection button.")

        # Define leagues to navigate to
        leagues = [
            'Kolmonen',
            'Kakkonen',
            'Liga Profesional Argentina',
            # Add more leagues here if needed
        ]

        season = 2024

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

        # Get fixture data
        fixture_data = fetch_fixtures()

        # Print non-started fixtures
        if fixture_data:
            data = json.loads(fixture_data)
            print(data)
        else:
            print("No non-started fixtures found.")

        for league in leagues:
            try:
                # Attempt to find and click on the league link        
                time.sleep(random.uniform(0.5, 1.0))  # Random sleep between 0.5 and 1.0 seconds
                league_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, league)))
                league_link.click()
                time.sleep(random.uniform(0.5, 1.0))  # Random sleep between 0.5 and 1.0 seconds

                # Retrieve team rankings
                team_element_list = driver.find_elements(By.XPATH, "//table[contains(@class,'leaguetable sortable table detailed-table')]/tbody/tr")
                
                num_teams = len(team_element_list)
                if num_teams == 0:
                    print(f"No teams found for league: {league}")
                    continue  # Skip if no teams are found

                # Initialize variables
                team_rankings = {}
                team_ids = []

                # Extract team rankings and details
                for team in team_element_list:
                    team_info = team.text.split()
                    numeric_indices = [i for i, item in enumerate(team_info) if item.isdigit()]
                    rank = int(team_info[0])
                    split_index = numeric_indices[1]
                    team_name = ' '.join(team_info[1:split_index])
                    team_rankings[team_name] = rank
                    team_id = team.get_attribute("data-team_id")
                    team_ids.append(team_id)

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

                        # Find the corresponding team_id for each team
                        try:
                            home_team_index = list(team_rankings.keys()).index(home_team)
                            away_team_index = list(team_rankings.keys()).index(away_team)
                            
                            home_team_id = team_ids[home_team_index]
                            away_team_id = team_ids[away_team_index]

                        except ValueError as e:
                            print(f"Error finding team ID: {e}")
                            continue

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

                            # Use the calculated values to determine the game rating
                            total_home_points = (placement_points_home + home_goal_points + home_recent_performance_points)
                            total_away_points = (placement_points_away + away_goal_points + away_recent_performance_points)

                            if total_home_points >= 3:
                                one_star_games.append((home_team, away_team))
                            elif total_home_points == 2:
                                two_star_games.append((home_team, away_team))
                            elif total_home_points == 1:
                                three_star_games.append((home_team, away_team))

            except NoSuchElementException as e:
                print(f"Element not found for league {league}: {e}")
            except TimeoutException as e:
                print(f"Timeout while processing league {league}: {e}")
            except Exception as e:
                print(f"An error occurred while processing league {league}: {e}")

        # Print the results
        print("One Star Games:")
        for game in one_star_games:
            print(game)
        print("\nTwo Star Games:")
        for game in two_star_games:
            print(game)
        print("\nThree Star Games:")
        for game in three_star_games:
            print(game)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
