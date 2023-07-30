import json, requests
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd
import os
import numpy as np
import time
import config
import logging

logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)


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


def isFullData(data):
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

lastSevenDays = [getDayStr(x) for x in range(1, 9)]
print(lastSevenDays)

df = pd.DataFrame()

foundData = 0
for dayStr in tqdm(lastSevenDays):
    link = getDataLink(dayStr)
    r = requests.get(link)
    if str(r.status_code)[0] != "2" or foundData >= 7:
        continue
    foundData += 1
    for name, data in r.json().items():
        if isFullData(data):
            #print(name)
            #print(len(data))
            itemDF = pd.DataFrame.from_dict(data)
            #display(itemDF)
            try:
                itemDF = itemDF.drop(["open_price", "closed_price", "donch_top", "donch_bot"], axis=1)
                itemDF = itemDF.fillna({"order_type" : "closed"})
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
                pass
    

countDF = df.groupby("name").count().reset_index()
popularItems = countDF[countDF["datetime"] == 21]["name"]
df = df[df["name"].isin(popularItems)]
df = df.sort_values(by="name")
itemListDF = pd.DataFrame.from_dict(itemList)

# Create a correspondence dictionary between item names and their IDs
item_name_to_id = {row["url_name"]: row["id"] for _, row in itemListDF.iterrows()}

df["item_id"] = df["name"].map(item_name_to_id)

df["order_type"] = df["order_type"].str.lower()
df.to_csv("allItemData.csv", index=False)

os.remove("allItemDataBackup.csv")

config.setConfigStatus("runningStatisticsScraper", False)
