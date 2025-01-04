from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import json
import pymysql as sql
import zipfile

#Extract downloaded zip fole in new folder
def extract_files_to_new_folder(zip_file_path, new_folder_name):
  # Create the new folder
  try:
    os.makedirs(new_folder_name)
    print(new_folder_name)
  except FileExistsError:
    print(f"Folder '{new_folder_name}' already exists.")

  # Extract files to the new folder
  with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(new_folder_name)

#Update the json file data to database
def update_sql (data):
    try:
        #Establich db connection
        connection = sql.connect(
            host="localhost",          # MySQL server host
            user="root",               # MySQL username
            password="mysql",          # MySQL password
            database="cricket",        # MySQL database name
        )
        cursor = connection.cursor()

        #Fetch match data and insert into database
        info = data['info']
        if info['outcome'].get('by'):
            outcome_by_runs = info['outcome']['by'].get('runs')
            outcome_by_wickets = info['outcome']['by'].get('wickets')
            if outcome_by_runs:
                outcome_by_wickets = None
            elif outcome_by_wickets:
                outcome_by_runs = None
        else:
            outcome_by_wickets = None
            outcome_by_runs = None

        if not info.get('event'):
            return
        #Query to insert data into matches table
        cursor.execute('''
        INSERT INTO Matches (
            city, date, event_name, match_number, gender, match_type,
            match_type_number, season, team_type, toss_winner, toss_decision,
            outcome_winner, outcome_by_wickets, outcome_by_runs
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            info.get('city'),
            info['dates'][0],
            info['event']['name'],
            info['event'].get('match_number'),
            info['gender'],
            info['match_type'],
            info['match_type_number'],
            info['season'],
            info['team_type'],
            info['toss'].get('winner'),
            info['toss']['decision'],
            info['outcome'].get('winner'),
            #None,  # No wickets information in the provided JSON
            #info['outcome']['by'].get('runs', 0)
            outcome_by_wickets,
            outcome_by_runs
        ))
        match_id = cursor.lastrowid #To maintain the match id

        # Insert into Teams and Players
        team_ids = {}
        #Iterate team and players data
        for team_name, players in info['players'].items():
            team_ids[team_name] = cursor.execute('select team_id from Teams where team_name = %s',(team_name,))
            if team_ids[team_name] == None or team_ids[team_name]<1:
                cursor.execute('INSERT INTO Teams (team_name) VALUES (%s)', (team_name,))
                team_id = cursor.lastrowid
                team_ids[team_name] = team_id

            for player_name in players:
                player_id = cursor.execute('select player_id from Players where player_name = %s',(player_name,))
                #print(player_id)
                if player_id == None or player_id<1:
                    cursor.execute('INSERT INTO Players (player_name, team_id) VALUES (%s, %s)', (player_name, team_ids[team_name]))

        # Insert into Innings
        #Iterate innings json data to get the all overs details
        for inning in data['innings']:
            team_name = inning['team']
            team_id = cursor.execute('select team_id from Teams where team_name = %s',(team_name,))
            target_info = data.get('target', None)
            if target_info:
                target_runs = target_info.get('runs', None)
                target_overs = target_info.get('overs', None)
            else:
                target_runs = None
                target_overs = None
            cursor.execute('''
            INSERT INTO Innings (match_id, team_id, target_runs, target_overs)
            VALUES (%s, %s, %s, %s)
            ''', (match_id, team_ids[team_name], target_runs, target_overs))

            # Insert into Deliveries
            for over_data in inning['overs']:
                over_number = over_data['over']
                for delivery in over_data['deliveries']:
                    batter = delivery['batter']
                    bowler = delivery['bowler']
                    non_striker = delivery['non_striker']
                    cursor.execute('SELECT player_id FROM Players WHERE player_name = %s', (batter,))
                    batter_id = cursor.fetchone()[0]
                    cursor.execute('SELECT player_id FROM Players WHERE player_name = %s', (bowler,))
                    bowler_id = cursor.fetchone()[0]
                    cursor.execute('SELECT player_id FROM Players WHERE player_name = %s', (non_striker,))
                    non_striker_id = cursor.fetchone()[0]
                    #print(inning_id,match_id)                    
                    cursor.execute('''
                    INSERT INTO Deliveries (
                        match_id,over_number, batter_id, bowler_id, non_striker_id,
                        runs_batter, runs_extras, runs_total,
                        wicket_player_out, wicket_kind
                    ) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        match_id,
                        over_number,
                        batter_id,
                        bowler_id,
                        non_striker_id,
                        delivery['runs']['batter'],
                        sum(delivery.get('extras', {}).values()) if 'extras' in delivery else 0,
                        delivery['runs']['total'],
                        delivery.get('wickets', [{}])[0].get('player_out', None) if 'wickets' in delivery else None,
                        delivery.get('wickets', [{}])[0].get('kind', None) if 'wickets' in delivery else None
                    ))
        # Commit to aplly the changes
        connection.commit()
    except sql.MySQLError as e:
        print(f"Error: {e}")
        update = None
    finally:
        if connection:
            #Close established sql connection to free up the connection
            cursor.close()
            connection.close() 


chrome_option = Options()
download_path = "D:\\Personal\\cricket_data"

if not os.path.exists(download_path):
    print("True")
    #Create new directory
    os.makedirs(download_path)

#Preference for file download path
prefs = {
    "download.default_directory": download_path,
    "download.prompt_for_download": False,        
    "profile.default_content_settings.popups": 0,
    "safebrowsing.enabled": True 
}
chrome_option.add_experimental_option("prefs",prefs)

#Create connection with chrome browser
driver = webdriver.Chrome(options=chrome_option)

driver.get("https://cricsheet.org/matches/") #Target url
time.sleep(2); #Wait to load full page

# scroll to the bottom
driver.execute_script("window.scrollTo(0,document.body.scrollHeight)");
time.sleep(2); #wait to complete data loading on the page

#Download file by click the hyperlink
odi_json_link = driver.find_element(By.XPATH, "//dt[text()='One-day internationals']/following-sibling::dd/a[contains(@href, 'odis_json.zip')]")
odi_json_link.click()

time.sleep(2) 

t20_json_link = driver.find_element(By.XPATH, "//dt[text()='T20 internationals']/following-sibling::dd/a[contains(@href, 't20s_json.zip')]")  
t20_json_link.click()

time.sleep(2) 

test_json_link = driver.find_element(By.XPATH, "//dt[text()='Test matches']/following-sibling::dd/a[contains(@href, 'tests_json.zip')]")
test_json_link.click()

time.sleep(5) 

driver.quit() #close the browser

#Extract the zip files
extract_files_to_new_folder("D:\\Personal\\cricket_data\\odis_json.zip", "D:\\Personal\\cricket_data\\Extract\\ODI")
extract_files_to_new_folder("D:\\Personal\\cricket_data\\t20s_json.zip","D:\\Personal\\cricket_data\\Extract\\T20")
extract_files_to_new_folder("D:\\Personal\\cricket_data\\tests_json.zip","D:\\Personal\\cricket_data\\Extract\\TEST")

folder_path = "D:\\Personal\\cricket_data\\Extract"

#Iterate all the files in th eextracted folder and call method to read json
for root, dirs, files in os.walk(folder_path):
    for file in files:
        #print("enter")
        #print(folder_path)
        if file.endswith(".json"):
            file_path = os.path.join(root, file)
            print(file_path)
            with open(file_path, 'r') as f:
                data = json.load(f)
                try:
                   update_sql(data)
                except sql.MySQLError as e:
                    print(f"Error : {e}")
