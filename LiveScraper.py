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
import customLogger

logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)

customLogger.clearFile("wfmAPICalls.log")
customLogger.clearFile("orderTracker.log")
customLogger.writeTo("orderTracker.log", "Started Live Scraper")

def ignoreItems(itemName):
    return itemName in config.blacklistedItems


def getWeekIncrease(df, row):
    weekDF = pd.DataFrame(df[(df.get("name") == row["name"]) & (df.get("order_type") == "closed")]
                         ).sort_values(by='datetime').reset_index().drop("index", axis=1)
    change = weekDF.loc[6, "median"] - weekDF.loc[0, "median"]
    return change

def getBuySellOverlap():

    try:
        df = pd.read_csv("allItemDataBackup.csv")
    except FileNotFoundError:
        try:
            df = pd.read_csv("allItemData.csv")
        except FileNotFoundError:
            config.setConfigStatus("runningLiveScraper", False)
            customLogger.writeTo("orderTracker.log", f"LiveScraper Stopped. No file called allItemData.csv or allItemDataBackup.csv found. Let the Stats Scraper run to completion")
            raise Exception("LiveScraper Stopped. No file called allItemData.csv or allItemDataBackup.csv found. Let the Stats Scraper run to completion.")

    #volFilter = 15
    #rangeFilter = 10

    averaged_df = df.drop(["datetime", "item_id"], axis=1)
    averaged_df = averaged_df.groupby(['name', 'order_type']).mean().reset_index()

    # Create your connection.
    con = sqlite3.connect('inventory.db')

    inventory = pd.read_sql_query("SELECT * FROM inventory", con)
    con.close()
    inventory = inventory[inventory.get("number") > 0]
    inventoryNames = inventory["name"].unique()

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
    dfFilter["weekPriceShift"] = dfFilter.apply(lambda row : getWeekIncrease(df, row), axis=1)
    if config.strictWhitelist:
        dfFilter = dfFilter[(dfFilter.get("name").isin(config.whitelistedItems))]
    else:
        dfFilter = dfFilter[((dfFilter.get("avg_price") < config.avgPriceCap) & (dfFilter.get("weekPriceShift") >= config.priceShiftThreshold)) | (dfFilter.get("name").isin(inventoryNames)) | (dfFilter.get("name").isin(config.whitelistedItems))]
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

buySellOverlap = getBuySellOverlap()


def updateDBPrice(itemName, listedPrice):
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    purchasePrice = cur.execute(f"SELECT SUM(purchasePrice) FROM inventory WHERE name='{itemName}'").fetchone()[0]
    number = cur.execute(f"SELECT SUM(number) FROM inventory WHERE name='{itemName}'").fetchone()[0]
    cur.execute(f"UPDATE inventory SET purchasePrice=?, number=?, listedPrice=? WHERE name=?", [purchasePrice, number, listedPrice, itemName])
    con.commit()
    con.close()

def getItemId(url_name):
    try:
        df = pd.read_csv("allItemDataBackup.csv")
    except FileNotFoundError:
        df = pd.read_csv("allItemData.csv")
    df = df.set_index("name")
    return df.loc[url_name, "item_id"].iloc[0]

def getItemRank(buySellOverlap, url_name):
    if np.isnan(buySellOverlap.loc[url_name, "mod_rank"]):
        return None
    else:
        return buySellOverlap.loc[url_name, "mod_rank"]

def deleteAllOrders():
    currentOrders = getOrders()
    for order in currentOrders["sell_orders"]:
        if config.getConfigStatus("runningLiveScraper") and not ignoreItems(order["item"]["url_name"]):
            #logging.debug(order)
            updateDBPrice(order["item"]["url_name"], None)
            deleteOrder(order["id"])
    for order in currentOrders["buy_orders"]:
        if config.getConfigStatus("runningLiveScraper") and not ignoreItems(order["item"]["url_name"]):
            deleteOrder(order["id"])

def getFilteredDF(item):
    r = warframeApi.get(f"https://api.warframe.market/v1/items/{item}/orders")
    customLogger.writeTo(
        "wfmAPICalls.log",
        f"GET:https://api.warframe.market/v1/items/{item}/orders\tResponse:{r.status_code}"
    )
    logging.debug(r)
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




def getMyOrderInformation(item, orderType, currentOrders):
    myOrdersDF = pd.DataFrame.from_dict(currentOrders[f'{orderType}_orders'])
    myOrderActive = False
        #inventory = pd.read_csv("inventory.csv")
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

def restructureLiveOrderDF(liveOrderDF):
    liveBuyerDF = liveOrderDF[liveOrderDF.get("order_type") == "buy"].sort_values(by="platinum", ascending = False)
    liveBuyerDF = liveBuyerDF[liveBuyerDF.get("username") != config.inGameName]
    liveSellerDF = liveOrderDF[liveOrderDF.get("order_type") == "sell"].sort_values(by="platinum", ascending = True)
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

def knapsack(items, max_weight):
    n = len(items)
    dp = [[0] * (max_weight + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(1, max_weight + 1):
            weight, value, item_name, order_id = items[i - 1]
            if weight <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - weight] + value)
            else:
                dp[i][w] = dp[i - 1][w]

    selected_items = []
    unselected_items = []
    w = max_weight
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected_items.append(items[i - 1])
            w -= items[i - 1][0]
        else:
            unselected_items.append(items[i - 1])  # Append the item name to the unselected_items list

    return dp[n][max_weight], selected_items, unselected_items

def get_new_buy_data(myBuyOrdersDF, response, itemStats):
    newBuyOrderDF = pd.DataFrame.from_dict(response["order"])
    if newBuyOrderDF.shape[0] != 0:
        newBuyOrderDF["url_name"] = newBuyOrderDF["item"]["url_name"]
        newBuyOrderDF = newBuyOrderDF.iloc[0].to_frame().T
        newBuyOrderDF["potential_profit"] = itemStats['closedAvg'] - newBuyOrderDF["platinum"]
            
    myBuyOrdersDF = pd.concat([newBuyOrderDF,myBuyOrdersDF], ignore_index=True, axis=0)
    return myBuyOrdersDF



def compareLiveOrdersWhenBuying(item, liveOrderDF, itemStats, currentOrders, myBuyOrdersDF, itemID, modRank, inventory):
    con = sqlite3.connect('inventory.db')

    inventory = pd.read_sql_query("SELECT * FROM inventory", con)
    con.close()
    inventory = inventory[inventory.get("number") > 0]
    if ignoreItems(item):
        logging.debug("Item Blacklisted.")
        return
    orderType = "buy"
    myOrderID, visibility, myPlatPrice, myOrderActive = getMyOrderInformation(item, orderType, currentOrders)
    liveBuyerDF, liveSellerDF, numBuyers, numSellers, priceRange = restructureLiveOrderDF(liveOrderDF)

    #probably don't want to be looking at this item right now if there's literally nobody interested in selling it.
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
            logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
            return
    elif numBuyers == 0:
        return

    bestBuyer = liveBuyerDF.iloc[0]
    closedAvgMetric = itemStats["closedAvg"] - bestBuyer["platinum"]
    postPrice = bestBuyer["platinum"]
    potentialProfit = closedAvgMetric - 1

    if postPrice > int(config.avgPriceCap):
        logging.debug("This item is higher than the price cap you set.")
        return
    if ((inventory[inventory["name"] == item]["number"].sum() > 1) and (closedAvgMetric < (20 + 5 * inventory[inventory["name"] == item]["number"].sum()))):
        logging.debug("You're holding too many of this item! Not putting up a buy order.")
        if myOrderActive:
            logging.debug("In fact you have a buy order up for this item! Deleting it.")
            deleteOrder(myOrderID)
        return
    
    if (closedAvgMetric >= 30 and priceRange >= 15) or priceRange >= 21:
        if myOrderActive:
            if (myPlatPrice != (postPrice)):
                #need to edit such that updated listing does not exceed budget
                logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
                updateListing(myOrderID, str(postPrice), 1, str(visibility), item, "buy")
                myBuyOrdersDF.loc[myBuyOrdersDF["url_name"] == item,"platinum"] = postPrice
                myBuyOrdersDF.loc[myBuyOrdersDF["url_name"] == item,"potential_profit"] = myBuyOrdersDF.loc[myBuyOrdersDF["url_name"] == item]["potential_profit"] - (postPrice - myPlatPrice)
                return myBuyOrdersDF
            else:
                updateListing(myOrderID, str(postPrice), 1, str(visibility), item, "buy")
                logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
                return
        else:
            # if limit_max_plat_listings(myBuyOrdersDF, postPrice):
            #     return

            # Convert DataFrame to a list of tuples (platinum, potential_profit, url_name, id)
            buyOrdersList = []
            if myBuyOrdersDF.shape[0] != 0:
                buyOrdersList = list(myBuyOrdersDF[['platinum', 'potential_profit', 'url_name', 'id']].itertuples(index=False, name=None))
            buyOrdersList.append((postPrice, potentialProfit, item, None))
            maxProfit, selectedBuyOrders, unselectedBuyOrders = knapsack(buyOrdersList, config.maxTotalPlatCap)

            selectedItemNames = [i[2] for i in selectedBuyOrders]
            logging.debug(f"The most optimal config provides a profit of {maxProfit}")
            if item in selectedItemNames:
                if unselectedBuyOrders:
                    unSelectedItemNames = [i[2] for i in unselectedBuyOrders]
                    myBuyOrdersDF = myBuyOrdersDF[~(myBuyOrdersDF["url_name"].isin(unSelectedItemNames))]

                    for unselectedItem in unselectedBuyOrders:
                        deleteOrder(unselectedItem[3])
                        logging.debug(f"DELETED BUY order for {unselectedItem[2]} since it is not as optimal")

                response = postOrder(itemID, orderType, str(postPrice), str(1), True, modRank, item)
                if response.status_code != 200:
                    return
                response = response.json()["payload"]
                myBuyOrdersDF = get_new_buy_data(myBuyOrdersDF, response, itemStats)
                logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
                return myBuyOrdersDF
            else:
                logging.debug(f"Item is too expensive or less optimal than current listings")
                return
    elif myOrderActive:
        logging.debug(f"Not a good time to have an order up on this item. Deleted {orderType} order for {myPlatPrice}")
        logging.debug(f"Current highest buyer is:{bestBuyer['platinum']}")
        deleteOrder(myOrderID)
        return


def compareLiveOrdersWhenSelling(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory):
    con = sqlite3.connect('inventory.db')

    inventory = pd.read_sql_query("SELECT * FROM inventory", con)
    con.close()
    inventory = inventory[inventory.get("number") > 0]
    orderType = "sell"
    myOrderID, visibility, myPlatPrice, myOrderActive = getMyOrderInformation(item, orderType, currentOrders)

    if (not (item in inventory["name"].unique())) and (not myOrderActive):
        return
    elif (not (item in inventory["name"].unique())):
        updateDBPrice(myOrderID, None)
        deleteOrder(myOrderID)
        logging.debug(f"Deleted sell order for {item} since this is not in your inventory.")
        return
    
    inventory = inventory[inventory["name"] == item]
    liveBuyerDF, liveSellerDF, numBuyers, numSellers, priceRange = restructureLiveOrderDF(liveOrderDF)

    #probably don't want to be looking at this item right now if there's literally nobody interested in selling it.
    avgCost = (inventory["purchasePrice"] * inventory["number"]).sum() / inventory["number"].sum()
    myQuantity = inventory["number"].sum()
    if numSellers == 0:
        postPrice = int(avgCost+30)
        if myOrderActive:
            updateDBPrice(item, postPrice)
            updateListing(myOrderID, postPrice, myQuantity, str(visibility), item, "sell")
            return
        else:
            postOrder(itemID, orderType, postPrice, str(myQuantity), str(True), modRank, item)
            updateDBPrice(item, postPrice)
            return
    bestSeller = liveSellerDF.iloc[0]
    postPrice = bestSeller['platinum']
    inventory = inventory[inventory.get("name") == item].reset_index()
    

    if bestSeller["platinum"] - avgCost <= -10:
        SelfTexting.send_push("EMERGENCY", f"The price of {item} is probably dropping and you should sell this to minimize losses asap")

    if avgCost + 10 > postPrice and numSellers >= 2:
        postPrice = max([avgCost + 10, liveSellerDF.iloc[1]['platinum']])
    else:
        postPrice = max([avgCost + 10, postPrice])
        
    if myOrderActive:
        if (myPlatPrice != (postPrice)):
            logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
            updateDBPrice(item, int(postPrice))
            updateListing(myOrderID, str(int(postPrice)), myQuantity, str(visibility), item, "sell")
            return
        
        else:
            updateDBPrice(item, int(myPlatPrice))
            updateListing(myOrderID, str(int(postPrice)), myQuantity, str(visibility), item, "sell")
            logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
            return
    else:
        response = postOrder(itemID, orderType, int(postPrice), str(myQuantity), str(True), modRank, item)
        updateDBPrice(item, int(postPrice))
        logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
        return

# def calculate_potential_profit(row):
#     item_url_name = row["item"]["url_name"]
#     item = buySellOverlap.loc[item_url_name]
#     return row["platinum"] - overlap_platinum


r = postOrder("56783f24cbfa8f0432dd89a2", "buy", 1, 1, str(False), None, "lex_prime_set")
if r.status_code == 401:
    config.setConfigStatus("runningLiveScraper", False)
    raise Exception(f"Invalid JWT Token")


deleteAllOrders()
interestingItems = list(buySellOverlap.index)

try:
    while config.getConfigStatus("runningLiveScraper"):
        

        con = sqlite3.connect('inventory.db')

        inventory = pd.read_sql_query("SELECT * FROM inventory", con)
        con.close()
        inventory = inventory[inventory.get("number") > 0]
        inventoryNames = list(inventory["name"].unique())

        buySellOverlap = getBuySellOverlap()
        interestingItems = list(buySellOverlap.index)

        

        currentOrders = getOrders()
        myBuyOrdersDF = pd.DataFrame.from_dict(currentOrders["buy_orders"])
        if myBuyOrdersDF.shape[0] != 0:
            myBuyOrdersDF["url_name"] = myBuyOrdersDF.apply(lambda row : row["item"]["url_name"], axis=1)
            myBuyOrdersDF = myBuyOrdersDF[myBuyOrdersDF["url_name"].isin(interestingItems)]
        if myBuyOrdersDF.shape[0] != 0:
            myBuyOrdersDF["potential_profit"] = myBuyOrdersDF.apply(lambda row: int(buySellOverlap.loc[row["item"]["url_name"], 'closedAvg']) - row["platinum"] , axis=1)

        mySellOrdersDF = pd.DataFrame.from_dict(currentOrders["sell_orders"])
        if mySellOrdersDF.shape[0] != 0:
            mySellOrdersDF["url_name"] = mySellOrdersDF.apply(lambda row : row["item"]["url_name"], axis=1)
        
        interestingItems += config.whitelistedItems
        interestingItems += inventoryNames

        interestingItems = list(set(interestingItems))
        
        logging.debug("Interesting Items:\n" + ", ".join(interestingItems).replace("_", " ").title())
        customLogger.writeTo("orderTracker.log", f"Interesting Items (Post-Whitelist):{' '.join(interestingItems)}")

        for item in interestingItems:
            if not config.getConfigStatus("runningLiveScraper"):
                break
            
            con = sqlite3.connect('inventory.db')

            inventory = pd.read_sql_query("SELECT * FROM inventory", con)
            con.close()
            inventory = inventory[inventory.get("number") > 0]
            #t = time.time()

            liveOrderDF = getFilteredDF(item)
            if liveOrderDF.empty:
                logging.debug("There was an error with seeing the live orders on this item.")
                continue

            if item not in list(buySellOverlap.index):
                r = warframeApi.get(f"https://api.warframe.market/v1/items/{item}")
                customLogger.writeTo("wfmAPICalls.log", f"GET:https://api.warframe.market/v1/items/{item}\tResponse:{r.status_code}")
                if r.status_code != 200:
                    continue

                itemID = r.json()["payload"]["item"]['id']
                try:
                    modRank = r.json()["payload"]["item"]["items_in_set"][0]['mod_max_rank']
                except KeyError:
                    modRank = None
                compareLiveOrdersWhenSelling(item, liveOrderDF, None, currentOrders, itemID, modRank, inventory)

                continue

            itemStats = buySellOverlap.loc[item]
            logging.debug(item.replace("_", " ").title() + f"(closedAvg: {round(itemStats['closedAvg'], 2)}):")
            
            itemID = getItemId(item)
            modRank = getItemRank(buySellOverlap, item)

            newBuyOrderDf = compareLiveOrdersWhenBuying(item, liveOrderDF, itemStats, currentOrders, myBuyOrdersDF, itemID, modRank, inventory)
            if isinstance(newBuyOrderDf, pd.DataFrame):
                myBuyOrdersDF = newBuyOrderDf
            compareLiveOrdersWhenSelling(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory)
            
            #compareLiveOrdersToData(item, liveOrderDF, "buy", itemStats, currentOrders, itemID, modRank, inventory)
            #compareLiveOrdersToData(item, liveOrderDF, "sell", itemStats, currentOrders, itemID, modRank, inventory)
            
            #logging.debug(item)
            #logging.debug(time.time() - t)

except OSError as err:
    config.setConfigStatus("runningLiveScraper", False)
    logging.debug("OS error:", err)
except Exception as err:
    config.setConfigStatus("runningLiveScraper", False)
    logging.debug(f"Unexpected {err=}, {type(err)=}")
    customLogger.writeTo("orderTracker.log", f"Error in LiveScraper: Unexpected {err=}, {type(err)=}")
    raise Exception(f"Unexpected {err=}, {type(err)=}")

config.setConfigStatus("runningLiveScraper", False)
