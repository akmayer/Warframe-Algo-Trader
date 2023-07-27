import sqlite3
import os
import json

# File creation and database connection
filename = "inventory.db"

# Check if the file exists; if not, create an empty file
if not os.path.exists(filename):
    with open(filename, "w"):
        pass  # Creating an empty file
    print(f"File '{filename}' created successfully!")
else:
    print(f"File '{filename}' already exists.")

# Connect to the SQLite database
con = sqlite3.connect('inventory.db')
cur = con.cursor()

# Create 'inventory' table if it doesn't exist
cur.execute('''CREATE TABLE if not exists inventory(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                purchasePrice REAL NOT NULL,
                listedPrice INTEGER,
                number INTEGER NOT NULL) STRICT;
                ''')

# Create 'transactions' table if it doesn't exist
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

# Configuration file handling
filename = "config.json"
config_data = {
    "pushbutton_token": "",
    "pushbutton_device_iden": "",
    "wfm_jwt_token": "",
    "inGameName" : "",
    "runningLiveScraper": False,
    "runningStatisticsScraper": False,
    "runningWarframeScreenDetect": False,
    "platform" : ""
}

# Check if the configuration file exists; if not, create it with default data
if not os.path.exists(filename):
    with open(filename, "w") as file:
        json.dump(config_data, file, indent=4)
    print(f"File '{filename}' created successfully!")
else:
    print(f"File '{filename}' already exists.")

# Directory creation
directory = "logs"

# Check if the 'logs' directory exists; if not, create it
if not os.path.exists(directory):
    os.makedirs(directory)
    print(f"Directory '{directory}' created successfully.")
else:
    print(f"Directory '{directory}' already exists.")
