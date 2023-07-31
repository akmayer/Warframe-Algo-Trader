import sqlite3
import os
import json

filename = "inventory.db"

if not os.path.exists(filename):
    with open(filename, "w"):
        pass  # Creating an empty file
    print(f"File '{filename}' created successfully!")
else:
    print(f"File '{filename}' already exists.")

con = sqlite3.connect('inventory.db')
cur = con.cursor()
# Connecting to the geeks database
 
# Creating a cursor object to execute
# SQL queries on a database table

# Table Definition
cur.execute('''CREATE TABLE if not exists inventory(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                purchasePrice REAL NOT NULL,
                listedPrice INTEGER,
                number INTEGER NOT NULL) STRICT;
                ''')

cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        datetime TEXT,
        transactionType TEXT,
        price INTEGER
    ) STRICT
""")
con.close()

filename = "config.json"
config_data = {
    "notif_platform": "",
    "pushbutton_token": "",
    "pushbutton_device_iden": "",
    "pushover_user_token": "",
    "pushover_application_token": "",
    "wfm_jwt_token": "",
    "inGameName" : "",
    "runningLiveScraper": False,
    "runningStatisticsScraper": False,
    "runningWarframeScreenDetect": False,
    "platform" : ""
}

if not os.path.exists(filename):
    with open(filename, "w") as file:
        json.dump(config_data, file, indent=4)
    print(f"File '{filename}' created successfully!")
else:
    print(f"File '{filename}' already exists.")


directory = "logs"

# Check if the directory already exists
if not os.path.exists(directory):
    # If it doesn't exist, create it
    os.makedirs(directory)
    print(f"Directory '{directory}' created successfully.")
else:
    print(f"Directory '{directory}' already exists.")