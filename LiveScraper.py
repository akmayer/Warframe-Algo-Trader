import json, requests, time
import pandas as pd
import sqlite3
import json, requests, time
from pprint import pprint
from IPython.display import clear_output
import sqlite3
from AccessingWFMarket import *
import SelfTexting
import config
import numpy as np
import logging

logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)


try:
    df = pd.read_csv("allItemDataBackup.csv")
except FileNotFoundError:
    df = pd.read_csv("allItemData.csv")

volFilter = 15
rangeFilter = 10

averaged_df = df.drop(["datetime", "item_id"], axis=1)
averaged_df = averaged_df.groupby(['name', 'order_type']).mean().reset_index()

def getWeekIncrease(row):
    weekDF = df[(df.get("name") == row["name"]) & (df.get("order_type") == "closed")].reset_index().drop("index", axis=1)
    change = weekDF.loc[0, "avg_price"] - weekDF.loc[6, "avg_price"]
    return change



# Create your connection.
con = sqlite3.connect('inventory.db')

inventory = pd.read_sql_query("SELECT * FROM inventory", con)
con.close()
inventory = inventory[inventory.get("number") > 0]
inventoryNames = inventory["name"].unique()
#display(inventory)

#TODO wrap this in a function so that dfFilter and buySellOverlap can be modified based on the inventory in the LiveScraper
dfFilter = averaged_df[(((averaged_df.get("volume") > volFilter) & (averaged_df.get("range") > rangeFilter)) | (averaged_df.get("name").isin(inventoryNames))) & (averaged_df.get("order_type") == "closed")]

dfFilter = dfFilter.sort_values(by="range", ascending=False)
dfFilter["weekPriceShift"] = dfFilter.apply(getWeekIncrease, axis=1)
dfFilter = dfFilter[((dfFilter.get("avg_price") < 400) & (dfFilter.get("weekPriceShift") >= -2)) | (dfFilter.get("name").isin(inventoryNames))]
    
names = dfFilter["name"].unique()

dfFiltered = averaged_df[averaged_df["name"].isin(names)]

dfFiltered = dfFiltered.set_index("name")
dfFilter = dfFilter.set_index("name")

#TODO wrap this in a function so that it can be called when re-evaluateing buy-sell overlap based on inventory
buySellOverlap = pd.DataFrame(dfFilter.index.unique(), columns=["name"])
buySellOverlap["minSell"] = buySellOverlap.apply(lambda row : dfFiltered.loc[dfFiltered["order_type"] == "sell"].loc[row["name"], "min_price"], axis=1)
buySellOverlap["maxBuy"] = buySellOverlap.apply(lambda row : dfFiltered.loc[dfFiltered["order_type"] == "buy"].loc[row["name"], "max_price"], axis=1)
buySellOverlap["overlap"] = buySellOverlap.apply(lambda row : row["maxBuy"] - row["minSell"], axis=1)
buySellOverlap["closedVol"] =  buySellOverlap.apply(lambda row : dfFilter.loc[row["name"], "volume"], axis=1)
buySellOverlap["closedMin"] = buySellOverlap.apply(lambda row : dfFilter.loc[row["name"], "min_price"], axis=1)
buySellOverlap["closedMax"] = buySellOverlap.apply(lambda row : dfFilter.loc[row["name"], "max_price"], axis=1)
buySellOverlap["closedAvg"] = buySellOverlap.apply(lambda row : dfFilter.loc[row["name"], "avg_price"], axis=1)
buySellOverlap["closedMedian"] = buySellOverlap.apply(lambda row : dfFilter.loc[row["name"], "median"], axis=1)
buySellOverlap["priceShift"] = buySellOverlap.apply(lambda row : dfFilter.loc[row["name"], "weekPriceShift"], axis=1)
buySellOverlap["mod_rank"] = buySellOverlap.apply(lambda row : dfFilter.loc[row["name"], "mod_rank"], axis=1)
buySellOverlap["item_id"] = buySellOverlap.apply(lambda row : df[df["name"] == row["name"]].reset_index().loc[0, "item_id"], axis=1)


buySellOverlap = buySellOverlap.set_index("name")


warframeApi = WarframeApi()


def updateDBPrice(itemName, listedPrice):
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    purchasePrice = cur.execute(f"SELECT SUM(purchasePrice) FROM inventory WHERE name='{itemName}'").fetchone()[0]
    number = cur.execute(f"SELECT SUM(number) FROM inventory WHERE name='{itemName}'").fetchone()[0]
    cur.execute(f"UPDATE inventory SET purchasePrice=?, number=?, listedPrice=? WHERE name=?", [purchasePrice, number, listedPrice, itemName])
    con.commit()
    con.close()

def getItemId(buySellOverlap, url_name):
    return buySellOverlap.loc[url_name, "item_id"]

def getItemRank(buySellOverlap, url_name):
    if np.isnan(buySellOverlap.loc[url_name, "mod_rank"]):
        return None
    else:
        return buySellOverlap.loc[url_name, "mod_rank"]

def deleteAllOrders():
    currentOrders = getOrders()
    for order in currentOrders["sell_orders"]:
        if config.getConfigStatus("runningLiveScraper"):
            #logging.debug(order)
            updateDBPrice(order["item"]["url_name"], None)
            deleteOrder(order["id"])
    for order in currentOrders["buy_orders"]:
        if config.getConfigStatus("runningLiveScraper"):
            deleteOrder(order["id"])

def getFilteredDF(item):
    r = warframeApi.get(f"https://api.warframe.market/v1/items/{item}/orders")
    try:
        data = r.json()
    except:
        logging.debug(r)
        return
    data = data["payload"]["orders"]
    df = pd.DataFrame.from_dict(data)
    df["status"] = df.apply(lambda row : row["user"]["status"], axis=1)
    df["username"] = df.apply(lambda row : row["user"]["ingame_name"], axis=1)
    df = df[df.get("status") == "ingame"]
    
    if "mod_rank" in df.columns:
        df = df[df.get("mod_rank") == pd.Series.max(df["mod_rank"])]
    else:
        pass
    return df


def ignoreItems(itemName):
    blacklistedItems = []
    return itemName in blacklistedItems

def compareLiveOrdersToData(item, liveOrderDF, orderType, itemStats, currentOrders, itemID, modRank, inventory):
    myOrdersDF = pd.DataFrame.from_dict(currentOrders[f'{orderType}_orders'])
    myOrderActive = False
    #inventory = pd.read_csv("inventory.csv")
    if myOrdersDF.shape[0] != 0:
        myOrdersDF["url_name"] = myOrdersDF.apply(lambda row : row["item"]["url_name"], axis=1)
        myOrdersDF = myOrdersDF[myOrdersDF.get("url_name") == item].reset_index()
    
    if myOrdersDF.shape[0] != 0:
        myOrderID = myOrdersDF.loc[0, "id"]
        visibility = myOrdersDF.loc[0, "visible"]
        myPlatPrice = myOrdersDF.loc[0, "platinum"]
        myOrderActive = True
    
    if orderType == "sell" and (not (item in inventory["name"].unique())) and (not myOrderActive):
        return
    
    orderDF = liveOrderDF[liveOrderDF.get("order_type") == orderType]
    if orderType == "buy":
        asc = False
        metricMult = 1
        liveMetricKey = "maxBuy"
        closedMetricKey = "closedMin"
    else:
        asc = True
        metricMult = -1
        liveMetricKey = "minSell"
        closedMetricKey = "closedMax"
    
    orderDF = orderDF.sort_values(by="platinum", ascending = asc).reset_index().drop("index", axis=1)
    orderDF = orderDF[orderDF.get("username") != "Yelbuzz"].reset_index().drop("index", axis=1)
    #display(orderDF)
    numTraders = orderDF.shape[0]
    #if no online buyers/sellers
    logging.debug(f"Week average {closedMetricKey}:\t{itemStats[closedMetricKey]}")
    if numTraders == 0:
        #send_push("No buyers active", f"There is no one {orderType}ing {item}. Log in and decide what to do yourself.")
        logging.debug(f"No {orderType}ers for this item!")
    else:
        bestTrader = orderDF.loc[0]
        liveOrderMetric = metricMult * (bestTrader["platinum"] - itemStats[liveMetricKey])
        closedOrderMetric = metricMult * (itemStats[closedMetricKey] - bestTrader["platinum"])
        closedAvgMetric = metricMult * (itemStats["closedAvg"] - bestTrader["platinum"])
        #if liveOrderMetric > 0:
            #logging.debug(f"GOOD {orderType.upper()}ER ACTIVE")
            #logging.debug(f"{bestTrader['username']}\t{bestTrader['platinum']}")
        postPrice = bestTrader['platinum']+metricMult

        '''if closedOrderMetric > 35:
            postPrice += 10'''
        
        if orderType == "buy":
            #if closedOrderMetric > 15:
            #    postPrice += 4
                
            if ((inventory[inventory["name"] == item]["number"].sum() > 1) and (closedOrderMetric < (6 + 4 * inventory[inventory["name"] == item]["number"].sum())) or ignoreItems(item)):
                logging.debug("You're holding too many of this item! Not putting up a buy order.")
                if myOrderActive:
                    logging.debug("In fact you have a buy order up for this item! Deleting it.")
                    deleteOrder(myOrderID)
                return
            
            if closedOrderMetric > 6 and closedAvgMetric > 10:
                if myOrderActive:
                    if (myPlatPrice != (postPrice)):
                        logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
                        updateListing(myOrderID, str(postPrice), 1, str(visibility))
                    else:
                        logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
                else:
                    postOrder(itemID, orderType, str(postPrice), str(1), True, modRank)
                    logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
            elif myOrderActive:
                logging.debug(f"Not a good time to have an order up on this item. Deleted {orderType} order for {myPlatPrice}")
                logging.debug(f"Current highest buyer is:{bestTrader['platinum']}")
                deleteOrder(myOrderID)
        
        elif orderType == "sell" and item in inventory["name"].unique():
            inventory = inventory[inventory.get("name") == item].reset_index()
            avgCost = (inventory["purchasePrice"] * inventory["number"]).sum() / inventory["number"].sum()

            if avgCost + 10 > postPrice:
                postPrice = max([avgCost + 10, orderDF.loc[1]['platinum']+metricMult])
            else:
                postPrice = max([avgCost + 10, postPrice])
                
            if myOrderActive:
                if (myPlatPrice != (postPrice)):
                    logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
                    updateDBPrice(item, int(postPrice))
                    updateListing(myOrderID, str(int(postPrice)), 1, str(visibility))
                else:
                    updateDBPrice(item, int(myPlatPrice))
                    logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
            else:
                response = postOrder(itemID, orderType, int(postPrice), str(1), str(True), modRank)
                updateDBPrice(item, int(postPrice))
                logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
        elif orderType == "sell" and myOrderActive:
            deleteOrder(myOrderID)
            logging.debug(f"Deleted sell order for {item} since this is not in your inventory.")
        else:
            logging.debug("You don't have any of this item in inventory to sell.")


deleteAllOrders()
interestingItems = list(buySellOverlap.index)

try:
    while config.getConfigStatus("runningLiveScraper"):
        logging.debug("Interesting Items:\n" + ", ".join(interestingItems).replace("_", " ").title())

        con = sqlite3.connect('inventory.db')

        inventory = pd.read_sql_query("SELECT * FROM inventory", con)
        con.close()
        inventory = inventory[inventory.get("number") > 0]

        #this line below doens't actually do anything since buySellOverlap is already filtered, this should be replaced with
        #a new DFFilter last line so hopefully some functions are made in StatsInterpreter for making DFFilter and buySellOverlap
        buySellOverlap = buySellOverlap[(buySellOverlap.get("priceShift") >= -2) | (buySellOverlap.index.isin(inventory["name"].unique()))]
        interestingItems = list(buySellOverlap.index)

        currentOrders = getOrders()
        myBuyOrdersDF = pd.DataFrame.from_dict(currentOrders["buy_orders"])
        if myBuyOrdersDF.shape[0] != 0:
            myBuyOrdersDF["url_name"] = myBuyOrdersDF.apply(lambda row : row["item"]["url_name"], axis=1)

        mySellOrdersDF = pd.DataFrame.from_dict(currentOrders["sell_orders"])
        if mySellOrdersDF.shape[0] != 0:
            mySellOrdersDF["url_name"] = mySellOrdersDF.apply(lambda row : row["item"]["url_name"], axis=1)

        for item in interestingItems:
            if not config.getConfigStatus("runningLiveScraper"):
                break
            
            con = sqlite3.connect('inventory.db')

            inventory = pd.read_sql_query("SELECT * FROM inventory", con)
            con.close()
            inventory = inventory[inventory.get("number") > 0]
            #t = time.time()

            itemStats = buySellOverlap.loc[item]
            logging.debug(item.replace("_", " ").title() + f"(closedAvg: {round(itemStats['closedAvg'], 2)}):")
            liveOrderDF = getFilteredDF(item)
            itemID = getItemId(buySellOverlap, item)
            modRank = getItemRank(buySellOverlap, item)
            
            compareLiveOrdersToData(item, liveOrderDF, "buy", itemStats, currentOrders, itemID, modRank, inventory)
            compareLiveOrdersToData(item, liveOrderDF, "sell", itemStats, currentOrders, itemID, modRank, inventory)
            
            logging.debug(item)
            #logging.debug(time.time() - t)

except OSError as err:
    config.setConfigStatus("runningLiveScraper", False)
    logging.debug("OS error:", err)
except Exception as err:
    config.setConfigStatus("runningLiveScraper", False)
    logging.debug(f"Unexpected {err=}, {type(err)=}")
    raise Exception(f"Unexpected {err=}, {type(err)=}")

config.setConfigStatus("runningLiveScraper", False)