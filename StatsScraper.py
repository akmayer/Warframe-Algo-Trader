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
logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)

# Fetch the list of all items from the Warframe Market API
allItemsLink = "https://api.warframe.market/v1/items"
r = requests.get(allItemsLink)
itemList = r.json()["payload"]["items"]

# Create a list of item names excluding those containing "relic"
itemNameList = [x["url_name"] for x in itemList if "relic" not in x["url_name"]]

# Create a dictionary to map item names to their URL names
urlLookup = {x["item_name"]: x["url_name"] for x in itemList}

csvFileName = "allItemData.csv"

# Backup the current CSV file (if exists) and handle any exceptions
try:
    os.rename(csvFileName, "allItemDataBackup.csv")
except FileNotFoundError:
    pass
except FileExistsError:
    config.setConfigStatus("runningStatisticsScraper", False)
    raise Exception("Remove the backup or the main csv file, one shouldn't be there for this to run.")

def isFullData(data):
    # Check if the data is full (either 3 or 6 data points)
    if len(data) == 0:
        return False
    if "mod_rank" in data[0].keys() and len(data) == 6:
        return True
    if "mod_rank" not in data[0].keys() and len(data) == 3:
        return True
    return False

def getDataLink(dayStr):
    # Create the data link based on the platform (PC or other)
    if config.platform != "pc":
        return f"https://relics.run/history/{config.platform}/price_history_{dayStr}.json"
    else:
        return f"https://relics.run/history/price_history_{dayStr}.json"

def getDayStr(daysBack):
    # Get the date string for a given number of days back from today
    day = datetime.now() - timedelta(daysBack)
    dayStr = datetime.strftime(day, '%Y-%m-%d')
    return dayStr

# Get the date strings for the last seven days
lastSevenDays = [getDayStr(x) for x in range(1, 9)]
print(lastSevenDays)

# Create an empty DataFrame to store the data
df = pd.DataFrame()

foundData = 0
for dayStr in tqdm(lastSevenDays):
    link = getDataLink(dayStr)
    r = requests.get(link)
    # Check if the request was successful and limit to a maximum of 7 data sets
    if str(r.status_code)[0] != "2" or foundData >= 7:
        # Log unsuccessful request and continue to the next day
        logging.warning(f"Failed to fetch data for {dayStr}, status code: {r.status_code}")
        continue
    foundData += 1
    for name, data in r.json().items():
        if isFullData(data):
            itemDF = pd.DataFrame.from_dict(data)
            try:
                # Clean up the data, add item name and range, and filter based on mod_rank
                itemDF = itemDF.drop(["open_price", "closed_price", "donch_top", "donch_bot"], axis=1)
                itemDF = itemDF.fillna({"order_type": "closed"})
                itemDF["name"] = urlLookup[name]
                itemDF["range"] = itemDF["max_price"] - itemDF["min_price"]
                if "mod_rank" not in itemDF.columns:
                    itemDF["mod_rank"] = np.nan
                else:
                    itemDF = itemDF[itemDF["mod_rank"] != 0]

                # Reorder the columns and concatenate the data to the main DataFrame
                itemDF = itemDF[["name", "datetime", "order_type", "volume", "min_price", "max_price", "range", "median", "avg_price", "mod_rank"]]
                df = pd.concat([df, itemDF])
            except KeyError:
                pass

# Perform data analysis and filtering
countDF = df.groupby("name").count().reset_index()
popularItems = countDF[countDF["datetime"] == 21]["name"]
df = df[df["name"].isin(popularItems)]
df = df.sort_values(by="name")
itemListDF = pd.DataFrame.from_dict(itemList)
df["item_id"] = df.apply(lambda row: itemListDF[itemListDF["url_name"] == row["name"]].reset_index().loc[0, "id"], axis=1)
df["order_type"] = df.get("order_type").str.lower()

# Save the final DataFrame to a CSV file
df.to_csv("allItemData.csv", index=False)

# Remove the backup CSV file
os.remove("allItemDataBackup.csv")

# Update the configuration status
config.setConfigStatus("runningStatisticsScraper", False)
