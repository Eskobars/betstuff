from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from datetime import datetime
import pandas as pd

def setup_driver():
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")  # Uncomment for headless mode
    driver = webdriver.Firefox(options=options)
    return driver

def main():
    driver = setup_driver()
    try:
        print("Loading the page...")
        driver.get('https://nr.soccerway.com/')
        
        wait = WebDriverWait(driver, 10)
        
        try:
            print("Attempting to reject cookies...")
            cookie_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-reject-all-handler']")))
            cookie_link.click()
            time.sleep(random.uniform(0.5, 1.0))
        except NoSuchElementException:
            print("Cookies already allowed or button not found. Skipping.")
        except TimeoutException:
            print("Timeout while trying to find the cookie rejection button.")
        
        leagues = ['Kolmonen', 'Kakkonen', 'Liga Profesional Argentina']
        season = 2024
        current_date = pd.Timestamp.now()
        epoch_time = datetime(1970, 1, 1)
        delta_seconds = int((current_date - epoch_time).total_seconds())
        one_day_epoch = 86400
        min_time = delta_seconds - one_day_epoch
        max_time = delta_seconds + one_day_epoch

        one_star_games = []
        two_star_games = []
        three_star_games = []

        for league in leagues:
            try:
                print(f"Processing league: {league}")

                time.sleep(random.uniform(1, 2.0))

                league_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, league)))
                league_link.click()

                time.sleep(random.uniform(3, 5))

                team_element_list = driver.find_elements(By.XPATH, "//table[contains(@class,'leaguetable sortable table detailed-table')]/tbody/tr")
                
                num_teams = len(team_element_list)
                if num_teams == 0:
                    print(f"No teams found for league: {league}")
                    continue

                time.sleep(random.uniform(2, 3))

                team_rankings = {}
                team_matches_played = {}
                team_ids = []
                
                for team in team_element_list:
                    team_info = team.text.split()
                    numeric_indices = [i for i, item in enumerate(team_info) if item.isdigit()]
                    rank = int(team_info[0])
                    split_index = numeric_indices[1]
                    team_name = ' '.join(team_info[1:split_index])
                    team_rankings[team_name] = rank

                      # Assuming the next numeric value after rank is the number of matches played
                    matches_played = int(team_info[split_index])
                    team_matches_played[team_name] = matches_played

                    team_id = team.get_attribute("data-team_id")
                    team_ids.append(team_id)

                worst_team_element = team_element_list[-1]
                worst_team_info = worst_team_element.text.split()
                worst_team_rank = int(worst_team_info[0])
                bottom_33_threshold = worst_team_rank - (num_teams // 3)

                element_list = driver.find_elements(By.XPATH, "//table[contains(@class,'matches')]/tbody/tr")
                for item in element_list:
                    item_text = item.text
                    if 'FT' in item_text:
                        continue
                    timestamp_attribute = item.get_attribute('data-timestamp')
                    if min_time <= int(timestamp_attribute) <= max_time:
                        if any(day in item_text for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                            continue
                        
                        team_names = item_text.split('\n')
                        home_team_name_fragment = team_names[1].lower().strip()
                        away_team_name_fragment = team_names[3].lower().strip()

                        # Helper function to find the best matching team name
                        def find_team_by_fragment(name_fragment, team_rankings):
                            for team_name in team_rankings.keys():
                                if name_fragment in team_name.lower():
                                    return team_name
                            return None

                        # Find the best matching team names
                        home_team = find_team_by_fragment(home_team_name_fragment, team_rankings)
                        away_team = find_team_by_fragment(away_team_name_fragment, team_rankings)

                        if home_team and away_team:
                            try:
                                home_team_index = list(team_rankings.keys()).index(home_team)
                                away_team_index = list(team_rankings.keys()).index(away_team)
                                
                                home_team_id = team_ids[home_team_index]
                                away_team_id = team_ids[away_team_index]
                            except ValueError as e:
                                print(f"Error finding team ID: {e}")
                                continue
                        else:
                            print(f"Could not find a matching team for: {home_team_name_fragment} or {away_team_name_fragment}")
                            continue

                        home_team_rank = team_rankings.get(home_team, None)
                        away_team_rank = team_rankings.get(away_team, None)

                        if home_team_rank is not None and away_team_rank is not None:
                            home_team_goal_difference = 0
                            away_team_goal_difference = 0
                            home_team_game_record = []
                            away_team_game_record = []
                            warnings = []

                            if home_team_rank >= bottom_33_threshold and away_team_rank >= bottom_33_threshold:
                                warnings.append("Both teams are in the bottom 33% of the league")

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

                            home_goal_points = 2 if home_team_goal_difference > 15 else 1 if 0 < home_team_goal_difference <= 15 else -1 if -15 < home_team_goal_difference <= 0 else -2
                            away_goal_points = 2 if away_team_goal_difference > 15 else 1 if 0 < away_team_goal_difference <= 15 else -1 if -15 < away_team_goal_difference <= 0 else -2

                            home_recent_performance_points = 2 if home_team_game_record[-5:] == ['W', 'W', 'W', 'W', 'W'] else -2 if home_team_game_record[-5:] == ['L', 'L', 'L', 'L', 'L'] else 1 if home_team_game_record[-3:] == ['W', 'W', 'W'] else -1 if home_team_game_record[-3:] == ['L', 'L', 'L'] else 0
                            away_recent_performance_points = 2 if away_team_game_record[-5:] == ['W', 'W', 'W', 'W', 'W'] else -2 if away_team_game_record[-5:] == ['L', 'L', 'L', 'L', 'L'] else 1 if away_team_game_record[-3:] == ['W', 'W', 'W'] else -1 if away_team_game_record[-3:] == ['L', 'L', 'L'] else 0

                              # Check the actual number of matches played by both teams
                            matches_played_threshold = 10
                            if any([team_matches_played.get(home_team, 0) <= matches_played_threshold,
                                    team_matches_played.get(away_team, 0) <= matches_played_threshold]):
                                warnings.append("The season just started.")

                            additional_points_home = 1
                            additional_points_away = -1

                            total_points_home = placement_points_home + home_goal_points + home_recent_performance_points + additional_points_home
                            total_points_away = placement_points_away + away_goal_points + away_recent_performance_points + additional_points_away

                            point_difference = abs(total_points_home - total_points_away)
                            if point_difference <= 2:
                                bet_rank = 1
                            elif point_difference <= 4:
                                bet_rank = 2
                            elif point_difference <= 6:
                                bet_rank = 3
                            else:
                                bet_rank = 0

                            winner = ""
                            if total_points_home > total_points_away and total_points_away < 0:
                                if point_difference >= 2:
                                    winner = home_team
                            elif total_points_away > total_points_home and total_points_home < 0:
                                if point_difference >= 2:
                                    winner = away_team

                            if winner:
                                combined_warning = " | ".join(warnings) if warnings else " "
                                game_info = {
                                    'Game Time': team_names[0],
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

                            print(f"Predicted Winner: {winner}")

                time.sleep(random.uniform(2, 3))

                # Go back to the main page
                driver.execute_script("window.history.go(-1)")
                time.sleep(random.uniform(2, 3))

            except NoSuchElementException:
                print(f"League '{league}' not found. Skipping.")
            except TimeoutException:
                print(f"Timeout while trying to find the league '{league}'. Skipping.")
                
    finally:
        driver.quit()

    print("1 Star Games:")
    for game in one_star_games:
        print(f"{game['Warning']} {game['Home Team']} vs {game['Away Team']}, Predicted Winner: {game['Predicted Winner']}, Points Home: {game['Points Home']}, Points Away: {game['Points Away']}")

    print("\n2 Star Games:")
    for game in two_star_games:
        print(f"{game['Warning']} {game['Game Time']}: {game['Home Team']} vs {game['Away Team']}, Predicted Winner: {game['Predicted Winner']}, Points Home: {game['Points Home']}, Points Away: {game['Points Away']}")

    print("\n3 Star Games:")
    for game in three_star_games:
        print(f"{game['Warning']} {game['Game Time']}: {game['Home Team']} vs {game['Away Team']}, Predicted Winner: {game['Predicted Winner']}, Points Home: {game['Points Home']}, Points Away: {game['Points Away']}")

    print("Press anything to quit")
    input()

if __name__ == "__main__":
    main()
