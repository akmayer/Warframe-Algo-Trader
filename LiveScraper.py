import json, requests, time
import pandas as pd
import sqlite3
from pprint import pprint
from IPython.display import clear_output
from AccessingWFMarket import *
import SelfTexting
import config
import numpy as np
import logging

logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)

# Function to calculate the price change over the last week for a given item.
def getWeekIncrease(row):
    try:
        df = pd.read_csv("allItemDataBackup.csv")
    except FileNotFoundError:
        df = pd.read_csv("allItemData.csv")
    weekDF = df[(df.get("name") == row["name"]) & (df.get("order_type") == "closed")].reset_index().drop("index", axis=1)
    change = weekDF.loc[0, "avg_price"] - weekDF.loc[6, "avg_price"]
    return change

# Function to get items with overlapping buy and sell orders, along with some additional filters.
def getBuySellOverlap():
    try:
        df = pd.read_csv("allItemDataBackup.csv")
    except FileNotFoundError:
        df = pd.read_csv("allItemData.csv")

    averaged_df = df.drop(["datetime", "item_id"], axis=1)
    averaged_df = averaged_df.groupby(['name', 'order_type']).mean().reset_index()

    # Create a connection to the local SQLite database containing inventory data.
    con = sqlite3.connect('inventory.db')

    # Fetch inventory data from the database.
    inventory = pd.read_sql_query("SELECT * FROM inventory", con)
    con.close()
    inventory = inventory[inventory.get("number") > 0]
    inventoryNames = inventory["name"].unique()

    # Filter the items based on specific criteria.
    dfFilter = averaged_df[(((averaged_df.get("volume") > config.volumeThreshold) & (averaged_df.get("range") > config.rangeThreshold)) | (averaged_df.get("name").isin(inventoryNames))) & (averaged_df.get("order_type") == "closed")]

    dfFilter = dfFilter.sort_values(by="range", ascending=False)
    if len(dfFilter) == 0:
        return pd.DataFrame.from_dict(
            {
                "name" : [],
                "minSell" : [],
                "maxBuy" : [],
                "overlap" : [],
                "closedVol" : [],
                "closedMin" : [],
                "closedMax" : [],
                "closedAvg" : [],
                "closedMedian" : [],
                "priceShift" : [],
                "mod_rank" : [],
                "item_id" : []
            }
        ).set_index("name")

    dfFilter["weekPriceShift"] = dfFilter.apply(getWeekIncrease, axis=1)
    dfFilter = dfFilter[((dfFilter.get("avg_price") < config.avgPriceCap) & (dfFilter.get("weekPriceShift") >= config.priceShiftThreshold)) | (dfFilter.get("name").isin(inventoryNames))]

    names = dfFilter["name"].unique()

    dfFiltered = averaged_df[averaged_df["name"].isin(names)]

    dfFiltered = dfFiltered.set_index("name")
    dfFilter = dfFilter.set_index("name")
    if len(dfFiltered.index.unique()) == 0:
        return pd.DataFrame.from_dict(
            {
                "name" : [],
                "minSell" : [],
                "maxBuy" : [],
                "overlap" : [],
                "closedVol" : [],
                "closedMin" : [],
                "closedMax" : [],
                "closedAvg" : [],
                "closedMedian" : [],
                "priceShift" : [],
                "mod_rank" : [],
                "item_id" : []
            }
        ).set_index("name")

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
    return buySellOverlap

# Function to update the listed price for an item in the database.
def updateDBPrice(itemName, listedPrice):
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    purchasePrice = cur.execute(f"SELECT SUM(purchasePrice) FROM inventory WHERE name='{itemName}'").fetchone()[0]
    number = cur.execute(f"SELECT SUM(number) FROM inventory WHERE name='{itemName}'").fetchone()[0]
    cur.execute(f"UPDATE inventory SET purchasePrice=?, number=?, listedPrice=? WHERE name=?", [purchasePrice, number, listedPrice, itemName])
    con.commit()
    con.close()

# Function to get the item ID from the provided URL name.
def getItemId(url_name):
    try:
        df = pd.read_csv("allItemDataBackup.csv")
    except FileNotFoundError:
        df = pd.read_csv("allItemData.csv")
    df = df.set_index("name")
    return df.loc[url_name, "item_id"].iloc[0]

# Function to get the mod rank of an item from the buySellOverlap DataFrame.
def getItemRank(buySellOverlap, url_name):
    if np.isnan(buySellOverlap.loc[url_name, "mod_rank"]):
        return None
    else:
        return buySellOverlap.loc[url_name, "mod_rank"]

# Function to delete all current orders (both buy and sell) in the game.
def deleteAllOrders():
    currentOrders = getOrders()
    for order in currentOrders["sell_orders"]:
        if config.getConfigStatus("runningLiveScraper"):
            updateDBPrice(order["item"]["url_name"], None)
            deleteOrder(order["id"])
    for order in currentOrders["buy_orders"]:
        if config.getConfigStatus("runningLiveScraper"):
            deleteOrder(order["id"])

# Function to get a filtered DataFrame for a specific item.
def getFilteredDF(item):
    r = warframeApi.get(f"https://api.warframe.market/v1/items/{item}/orders")
    try:
        data = r.json()
    except:
        return pd.DataFrame()
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

# Function to check if an item should be ignored based on the blacklisted items in the config.
def ignoreItems(itemName):
    return itemName in config.blacklistedItems

# Function to get information about the user's order for a specific item (buy or sell).
def getMyOrderInformation(item, orderType, currentOrders):
    myOrdersDF = pd.DataFrame.from_dict(currentOrders[f'{orderType}_orders'])
    myOrderActive = False
    myOrderID = None
    visibility = None
    myPlatPrice = None

    if myOrdersDF.shape[0] != 0:
        myOrdersDF["url_name"] = myOrdersDF.apply(lambda row : row["item"]["url_name"], axis=1)
        myOrdersDF = myOrdersDF[myOrdersDF.get("url_name") == item].reset_index()

    if myOrdersDF.shape[0] != 0:
        myOrderID = myOrdersDF.loc[0, "id"]
        visibility = myOrdersDF.loc[0, "visible"]
        myPlatPrice = myOrdersDF.loc[0, "platinum"]
        myOrderActive = True

    return myOrderID, visibility, myPlatPrice, myOrderActive

# Function to restructure the live order DataFrame into separate buyer and seller DataFrames.
def restructureLiveOrderDF(liveOrderDF):
    liveBuyerDF = liveOrderDF[liveOrderDF.get("order_type") == "buy"].sort_values(by="platinum", ascending=False)
    liveBuyerDF = liveBuyerDF[liveBuyerDF.get("username") != config.inGameName]
    liveSellerDF = liveOrderDF[liveOrderDF.get("order_type") == "sell"].sort_values(by="platinum", ascending=True)
    liveSellerDF = liveSellerDF[liveSellerDF.get("username") != config.inGameName]

    numBuyers, numSellers = liveBuyerDF.shape[0], liveSellerDF.shape[0]

    if numBuyers == 0:
        lowPrice = 0
    else:
        lowPrice = liveBuyerDF.iloc[0]["platinum"]

    if numSellers == 0:
        highPrice = None
        priceRange = None
    else:
        highPrice = liveSellerDF.iloc[0]["platinum"]
        priceRange = highPrice - lowPrice

    return liveBuyerDF, liveSellerDF, numBuyers, numSellers, priceRange

# Function to compare live buy orders for a specific item and take appropriate actions.
def compareLiveOrdersWhenBuying(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory):
    orderType = "buy"
    myOrderID, visibility, myPlatPrice, myOrderActive = getMyOrderInformation(item, orderType, currentOrders)
    liveBuyerDF, liveSellerDF, numBuyers, numSellers, priceRange = restructureLiveOrderDF(liveOrderDF)

    # Probably don't want to be looking at this item right now if there's literally nobody interested in selling it.
    if numSellers == 0:
        return
    bestSeller = liveSellerDF.iloc[0]
    if numBuyers == 0 and itemStats["closedAvg"] > 25:
        postPrice = max([priceRange-40, int(priceRange / 3) - 1])
        if postPrice > int(config.avgPriceCap):
            logging.debug("This item is higher than the price cap you set.")
            return
        if postPrice < 1:
            postPrice = 1
        if myOrderActive:
            updateListing(myOrderID, postPrice, 1, str(visibility), item, "buy")
            return
        else:
            postOrder(itemID, orderType, postPrice, 1, True, modRank, item)
            return
    elif numBuyers == 0:
        return

    bestBuyer = liveBuyerDF.iloc[0]
    closedAvgMetric = itemStats["closedAvg"] - bestBuyer["platinum"]
    postPrice = bestBuyer["platinum"]
    if postPrice > int(config.avgPriceCap):
        logging.debug("This item is higher than the price cap you set.")
        return
    if ((inventory[inventory["name"] == item]["number"].sum() > 1) and (closedAvgMetric < (20 + 5 * inventory[inventory["name"] == item]["number"].sum())) or ignoreItems(item)):
        logging.debug("You're holding too many of this item! Not putting up a buy order.")
        if myOrderActive:
            logging.debug("In fact you have a buy order up for this item! Deleting it.")
            deleteOrder(myOrderID)
        return

    if (closedAvgMetric >= 30 and priceRange >= 15) or priceRange >= 21 or closedAvgMetric >= 35:
        if myOrderActive:
            if (myPlatPrice != (postPrice)):
                logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
                updateListing(myOrderID, str(postPrice), 1, str(visibility), item, "buy")
                return
            else:
                updateListing(myOrderID, str(postPrice), 1, str(visibility), item, "buy")
                logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
                return
        else:
            postOrder(itemID, orderType, str(postPrice), str(1), True, modRank, item)
            logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
            return
    elif myOrderActive:
        logging.debug(f"Not a good time to have an order up on this item. Deleted {orderType} order for {myPlatPrice}")
        logging.debug(f"Current highest buyer is:{bestBuyer['platinum']}")
        deleteOrder(myOrderID)
        return

# Function to compare live sell orders for a specific item and take appropriate actions.
def compareLiveOrdersWhenSelling(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory):
    orderType = "sell"
    myOrderID, visibility, myPlatPrice, myOrderActive = getMyOrderInformation(item, orderType, currentOrders)

    if (not (item in inventory["name"].unique())) and (not myOrderActive):
        logging.debug("You don't have any of this item in inventory to sell.")
        return
    elif (not (item in inventory["name"].unique())):
        updateDBPrice(myOrderID, None)
        deleteOrder(myOrderID)
        logging.debug(f"Deleted sell order for {item} since this is not in your inventory.")
        return

    inventory = inventory[inventory["name"] == item]
    liveBuyerDF, liveSellerDF, numBuyers, numSellers, priceRange = restructureLiveOrderDF(liveOrderDF)

    # Probably don't want to be looking at this item right now if there's literally nobody interested in selling it.
    avgCost = (inventory["purchasePrice"] * inventory["number"]).sum() / inventory["number"].sum()
    if numSellers == 0:
        postPrice = int(avgCost+30)
        if myOrderActive:
            updateDBPrice(item, postPrice)
            updateListing(myOrderID, postPrice, 1, str(visibility), item, "sell")
            return
        else:
            postOrder(itemID, orderType, postPrice, str(1), str(True), modRank, item)
            updateDBPrice(item, postPrice)
            return
    bestSeller = liveSellerDF.iloc[0]
    closedAvgMetric = bestSeller["platinum"] - itemStats["closedAvg"]
    postPrice = bestSeller['platinum']
    inventory = inventory[inventory.get("name") == item].reset_index()

    if bestSeller["platinum"] - avgCost <= 0:
        SelfTexting.send_push("EMERGENCY", f"The price of {item} is probably dropping and you should sell this to minimize losses asap")

    if avgCost + 10 > postPrice and numSellers >= 2:
        postPrice = max([avgCost + 10, liveSellerDF.iloc[1]['platinum']])
    else:
        postPrice = max([avgCost + 10, postPrice])

    if myOrderActive:
        if (myPlatPrice != (postPrice)):
            logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
            updateDBPrice(item, int(postPrice))
            updateListing(myOrderID, str(int(postPrice)), 1, str(visibility), item, "sell")
            return

        else:
            updateDBPrice(item, int(myPlatPrice))
            updateListing(myOrderID, str(int(postPrice)), 1, str(visibility), item, "sell")
            logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
            return
    else:
        response = postOrder(itemID, orderType, int(postPrice), str(1), str(True), modRank, item)
        updateDBPrice(item, int(postPrice))
        logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
        return

# Main logic of the script.
try:
    while config.getConfigStatus("runningLiveScraper"):

        con = sqlite3.connect('inventory.db')

        inventory = pd.read_sql_query("SELECT * FROM inventory", con)
        con.close()
        inventory = inventory[inventory.get("number") > 0]

        buySellOverlap = getBuySellOverlap()
        interestingItems = list(buySellOverlap.index)

        logging.debug("Interesting Items:\n" + ", ".join(interestingItems).replace("_", " ").title())

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

            itemStats = buySellOverlap.loc[item]
            logging.debug(item.replace("_", " ").title() + f"(closedAvg: {round(itemStats['closedAvg'], 2)}):")
            liveOrderDF = getFilteredDF(item)
            if liveOrderDF.empty:
                logging.debug("There was an error with seeing the live orders on this item.")
                continue
            itemID = getItemId(item)
            modRank = getItemRank(buySellOverlap, item)

            compareLiveOrdersWhenBuying(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory)
            compareLiveOrdersWhenSelling(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory)

except OSError as err:
    config.setConfigStatus("runningLiveScraper", False)
    logging.debug("OS error:", err)
except Exception as err:
    config.setConfigStatus("runningLiveScraper", False)
    logging.debug(f"Unexpected {err=}, {type(err)=}")
    raise Exception(f"Unexpected {err=}, {type(err)=}")

config.setConfigStatus("runningLiveScraper", False)
