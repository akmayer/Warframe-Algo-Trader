# Import required libraries
import json, requests
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd
import os
import numpy as np
import time
import config
import logging

# Set up logging configuration
current_directory = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_directory, "Statsscraper.logs")

logging.basicConfig(level=logging.DEBUG, format='{levelname:7} {message}', style='{',
                    handlers=[
                        logging.FileHandler(log_file_path),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger(__name__)

# Fetch item data from the Warframe Market API
allItemsLink = "https://api.warframe.market/v1/items"
r = requests.get(allItemsLink)
itemList = r.json()["payload"]["items"]
itemNameList = [x["url_name"] for x in itemList if "relic" not in x["url_name"]]
urlLookup = {x["item_name"]: x["url_name"] for x in itemList}

# Set file names for the main and backup CSV files
csvFileName = "allItemData.csv"
backupCsvFileName = "allItemDataBackup.csv"

# Create a backup of the main CSV file if it already exists
try:
    os.rename(csvFileName, backupCsvFileName)
    logger.info("Created a backup of the main CSV file.")
except FileNotFoundError:
    pass
except FileExistsError:
    config.setConfigStatus("runningStatisticsScraper", False)
    raise Exception("Remove the backup or the main CSV file. Only one should be present for this script to run.")

# Helper function to check if data is complete
def is_Full_Data(data):
    if len(data) == 0:
        return False
    if "mod_rank" in data[0].keys() and len(data) == 6:
        return True
    if "mod_rank" not in data[0].keys() and len(data) in [3, 4]:
        return True
    return False

# Helper function to construct data link for a given day
def getDataLink(dayStr):
    if config.platform != "pc":
        return f"https://relics.run/history/{config.platform}/price_history_{dayStr}.json"
    else:
        return f"https://relics.run/history/price_history_{dayStr}.json"

# Helper function to get the date string for a given number of days back
def getDayStr(daysBack):
    day = datetime.now() - timedelta(daysBack)
    dayStr = datetime.strftime(day, '%Y-%m-%d')
    return dayStr

# Define the number of days for which data is to be fetched
DAY_COUNT = 7
last_seven_days = [getDayStr(x) for x in range(1, DAY_COUNT + 1)]

# Initialize an empty DataFrame to store the data
df = pd.DataFrame()
found_data = 0

# Dictionary to map item subtypes to their names
name_to_subtype = {
    "radiant": "radiant",
    "intact": "intact",
    "flawless": "flawless"
}

# Function to process item data and create DataFrames for each item
def process_item_data(data, item_name):
    try:
        item_df = pd.DataFrame.from_dict(data)
        required_keys = {"datetime", "volume", "min_price", "max_price"}
        missing_keys = required_keys.difference(item_df.columns)
        if missing_keys:
            logger.warning(f"Skipping incomplete data for {item_name} on {day_str} due to missing keys: {missing_keys}.")
            return None
        
        columns_to_drop = ["open_price", "closed_price", "donch_top", "donch_bot"]
        columns_to_drop = [col for col in columns_to_drop if col in item_df.columns]
        itemDF = item_df.drop(columns_to_drop, axis=1)

        itemDF = itemDF.fillna({"order_type": "closed"})
        itemDF["name"] = urlLookup[item_name]
        itemDF["range"] = itemDF["max_price"] - itemDF["min_price"]
        if "mod_rank" not in itemDF.columns:
            itemDF["mod_rank"] = np.nan
        else:
            itemDF = itemDF[itemDF["mod_rank"] != 0]

        itemDF = itemDF[["name", "datetime", "order_type", "volume", "min_price", "max_price", "range", "median", "avg_price", "mod_rank"]]
        return itemDF
    except Exception as e:
        logger.warning(f"Error processing data for {item_name} on {day_str}: {e}")
        return None

# Loop through the last seven days to fetch and process item data
for day_str in tqdm(last_seven_days):
    link = getDataLink(day_str)
    response = requests.get(link)
    if str(response.status_code)[0] != "2" or found_data >= 7:
        continue
    found_data += 1
    for name, data in response.json().items():
        if is_Full_Data(data):
            itemDF = process_item_data(data, name)
            if itemDF is not None:
                df = pd.concat([df, itemDF])

# Filter out items with insufficient data and select popular items
countDF = df.groupby("name").count().reset_index()
popularItems = countDF[countDF["datetime"] == 21]["name"]
df = df[df["name"].isin(popularItems)]
df = df.sort_values(by="name")
itemListDF = pd.DataFrame.from_dict(itemList)
df["item_id"] = df.apply(lambda row : itemListDF[itemListDF["url_name"] == row["name"]].reset_index().loc[0, "id"], axis=1)
df["order_type"] = df.get("order_type").str.lower()

# Save the data to CSV file
df.to_csv("allItemData.csv", index=False)

try:
    df.to_csv(csvFileName, index=False)
    logger.info("Data saved to CSV file.")
except Exception as e:
    logger.error(f"Failed to save data to CSV file: {e}")

# Remove the backup CSV file and mark the script as not running in the configuration
if os.path.exists(backupCsvFileName):
    os.remove(backupCsvFileName)
    logger.info("Backup CSV file removed.")
config.setConfigStatus("runningStatisticsScraper", False)

# End of the script
logger.info("Script execution completed.")
