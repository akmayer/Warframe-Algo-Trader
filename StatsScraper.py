import json, requests
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd
import os
import numpy as np
import time
import config

allItemsLink = "https://api.warframe.market/v1/items"
r = requests.get(allItemsLink)
itemList = r.json()["payload"]["items"]
itemNameList = [x["url_name"] for x in itemList]



csvFileName = "allItemData.csv"

try:
    os.rename(csvFileName, "allItemDataBackup.csv")
except FileNotFoundError:
    pass
except FileExistsError:
    config.setConfigStatus("runningStatisticsScraper", False)
    raise Exception("Remove the backup or the main csv file, one shouldn't be there for this to run.")

day = datetime.now() - timedelta(1)
dayStr = datetime.strftime(day, '%Y-%m-%d')
print(dayStr)
daysBack = 7

f = open(csvFileName, "w")
f.write("name,datetime,order_type,volume,min_price,max_price,range,median,avg_price,mod_rank\n")
f.close()

for i, item in enumerate(tqdm(sorted(itemNameList))):
    #f = open(csvFileName, "a")
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
    }
    t = time.time()
    r = requests.get(f"https://api.warframe.market/v1/items/{item}/statistics", headers=headers)
    #print(time.time() - t)
    #time.sleep(2)
    itemData = r.json()
    itemDataList = itemData["payload"]["statistics_live"]['90days']
    closedItemDataList = itemData["payload"]["statistics_closed"]['90days']
    closedItemDataList = list(reversed(closedItemDataList))
    itemDataList = list(reversed(itemDataList))
    
    day = datetime.now() - timedelta(daysBack)
    dayStr = datetime.strftime(day, '%Y-%m-%d')
    
    today = datetime.strftime(datetime.now(), '%Y-%m-%d')
    
    df = pd.DataFrame.from_dict(closedItemDataList)
    
    try:
        df = df[(df.get("datetime") > dayStr) & (df.get("datetime") < today)]
        #display(df)
    except:
        continue
    
    if "mod_rank" in df.columns:
        df = df[df.get("mod_rank") > 0]
    else:
        df["mod_rank"] = np.nan
    
    if (df.shape[0] != 7):
        continue
    
    df["name"] = item
    df["order_type"] = "closed"
    df["range"] = df["max_price"] - df["min_price"]
    df = df[["name", "datetime", "order_type", "volume", "min_price", "max_price","range", "median", "avg_price", "mod_rank"]]
    #display(df)
    
    df.to_csv(csvFileName, mode='a', index=False, header=False)
    
    df = pd.DataFrame.from_dict(itemDataList)
    try:
        df = df[(df.get("datetime") > dayStr) & (df.get("datetime") < today)]
    except:
        continue

    if "mod_rank" in df.columns:
        df = df[df.get("mod_rank") > 0]
    else:
        df["mod_rank"] = np.nan
    
    if (df.shape[0] != 14):
        continue
    
    df["name"] = item
    df["range"] = df["max_price"] - df["min_price"]
    df = df[["name", "datetime", "order_type", "volume", "min_price", "max_price","range", "median", "avg_price", "mod_rank"]]
    #display(df)
    
    df.to_csv(csvFileName, mode='a', index=False, header=False)
    
    #f.close()

itemListDF = pd.DataFrame.from_dict(itemList)
#itemListDF
df = pd.read_csv("allItemData.csv")
#df = df.drop("Unnamed: 0", axis=1)
df["item_id"] = df.apply(lambda row : itemListDF[itemListDF["url_name"] == row["name"]].reset_index().loc[0, "id"], axis=1)
#df
df.to_csv("allItemData.csv", index=False)

try:
    os.remove("allItemDataBackup.csv")
except FileNotFoundError:
    pass

config.setConfigStatus("runningStatisticsScraper", False)