import json, requests
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd
import os
import numpy as np
import time
import config
import logging

current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the log file path
log_file_path = os.path.join(current_directory, "Statsscraper.logs")

# Configure logging settings
logging.basicConfig(level=logging.DEBUG, format='{levelname:7} {message}', style='{',
                    handlers=[
                        logging.FileHandler(log_file_path),
                        logging.StreamHandler()
                    ])

# Set up the logger
logger = logging.getLogger(__name__)

allItemsLink = "https://api.warframe.market/v1/items"
r = requests.get(allItemsLink)
itemList = r.json()["payload"]["items"]
itemNameList = [x["url_name"] for x in itemList if "relic" not in x["url_name"]]
urlLookup = {x["item_name"] : x["url_name"] for x in itemList}

csvFileName = "allItemData.csv"

try:
    os.rename(csvFileName, "allItemDataBackup.csv")
except FileNotFoundError:
    pass
except FileExistsError:
    config.setConfigStatus("runningStatisticsScraper", False)
    raise Exception("Remove the backup or the main csv file, one shouldn't be there for this to run.")


def is_Full_Data(data):
    if len(data) == 0:
        return False
    if "mod_rank" in data[0].keys() and len(data) == 6:
        return True
    if "mod_rank" not in data[0].keys() and len(data) == 3:
        return True
    return False

def getDataLink(dayStr):
    if config.platform != "pc":
        return f"https://relics.run/history/{config.platform}/price_history_{dayStr}.json"
    else:
        return f"https://relics.run/history/price_history_{dayStr}.json"

def getDayStr(daysBack):
    day = datetime.now() - timedelta(daysBack)
    dayStr = datetime.strftime(day, '%Y-%m-%d')
    return dayStr

# Define the number of days to retrieve data for
DAY_COUNT = 7
last_seven_days = [getDayStr(x) for x in range(1, DAY_COUNT + 1)]
df = pd.DataFrame()
found_data = 0

# Loop through the last seven days and scrape data from each day
for day_str in tqdm(last_seven_days):
    link = getDataLink(day_str)
    response = requests.get(link)
    if str(response.status_code)[0] != "2" or found_data >= 7:
        # If there was an error or we already found data for 7 days, continue to the next day
        continue
    found_data += 1
    for name, data in response.json().items():
        if is_Full_Data(data):
            # Create a DataFrame from the fetched data and process it
            item_df = pd.DataFrame.from_dict(data)
            try:
                itemDF = item_df.drop(["open_price", "closed_price", "donch_top", "donch_bot"], axis=1)
                itemDF = item_df.fillna({"order_type" : "closed"})
                itemDF["name"] = urlLookup[name]
                itemDF["range"] = itemDF["max_price"] - itemDF["min_price"]
                if "mod_rank" not in itemDF.columns:
                    itemDF["mod_rank"] = np.nan
                else:
                    itemDF = itemDF[itemDF["mod_rank"] != 0]
                #display(itemDF)
                
                itemDF = itemDF[["name", "datetime", "order_type", "volume", "min_price", "max_price","range", "median", "avg_price", "mod_rank"]]
                
                df = pd.concat([df, itemDF])
            except KeyError:
                logger.warning(f"Skipping incomplete data for {name} on {day_str} due to missing keys.")
    

countDF = df.groupby("name").count().reset_index()
popularItems = countDF[countDF["datetime"] == 21]["name"]
df = df[df["name"].isin(popularItems)]
df = df.sort_values(by="name")
itemListDF = pd.DataFrame.from_dict(itemList)
#itemListDF
#df = df.drop("Unnamed: 0", axis=1)
df["item_id"] = df.apply(lambda row : itemListDF[itemListDF["url_name"] == row["name"]].reset_index().loc[0, "id"], axis=1)
df["order_type"] = df.get("order_type").str.lower()
df.to_csv("allItemData.csv", index=False)

# Save the scraped data to a CSV file
try:
    df.to_csv(csvFileName, index=False)
    logger.info("Data saved to CSV file.")
except Exception as e:
    logger.error(f"Failed to save data to CSV file: {e}")

# Remove the backup CSV file and mark the script as not running in the configuration
    os.remove("allItemDataBackup.csv")
    config.setConfigStatus("runningStatisticsScraper", False)
# End of the script
logger.info("Script execution completed.")
