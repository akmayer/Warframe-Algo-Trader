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

#volFilter = 15
#rangeFilter = 10

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
dfFilter = averaged_df[(((averaged_df.get("volume") > config.volumeThreshold) & (averaged_df.get("range") > config.rangeThreshold)) | (averaged_df.get("name").isin(inventoryNames))) & (averaged_df.get("order_type") == "closed")]

dfFilter = dfFilter.sort_values(by="range", ascending=False)
dfFilter["weekPriceShift"] = dfFilter.apply(getWeekIncrease, axis=1)
dfFilter = dfFilter[((dfFilter.get("avg_price") < config.avgPriceCap) & (dfFilter.get("weekPriceShift") >= config.priceShiftThreshold)) | (dfFilter.get("name").isin(inventoryNames))]
    
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
    return itemName in config.blacklistedItems

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


def getLivePriceRange(liveOrderDF, numBuyers, numSellers):
    if numBuyers == 0:
        lowPrice = 0
    else:
        lowPrice = liveOrderDF[liveOrderDF.get("order_type") == "sell"]

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
        


def compareLiveOrdersWhenBuying(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory):
    orderType = "buy"
    myOrderID, visibility, myPlatPrice, myOrderActive = getMyOrderInformation(item, orderType, currentOrders)
    liveBuyerDF, liveSellerDF, numBuyers, numSellers, priceRange = restructureLiveOrderDF(liveOrderDF)

    #probably don't want to be looking at this item right now if there's literally nobody interested in selling it.
    if numSellers == 0:
        return
    bestSeller = liveSellerDF.iloc[0]
    if numBuyers == 0 and itemStats["closedAvg"] > 25:
        postPrice = max([priceRange-40, int(priceRange / 3) - 1])
        if postPrice < 1:
            postPrice = 1
        if myOrderActive:
            updateListing(myOrderID, postPrice, 1, str(visibility))
            return
        else:
            postOrder(itemID, orderType, postPrice, 1, True, modRank)
            return
    elif numBuyers == 0:
        return

    bestBuyer = liveBuyerDF.iloc[0]
    closedAvgMetric = itemStats["closedAvg"] - bestBuyer["platinum"]
    postPrice = bestBuyer["platinum"] + 1
    if ((inventory[inventory["name"] == item]["number"].sum() > 1) and (closedAvgMetric < (15 + 5 * inventory[inventory["name"] == item]["number"].sum())) or ignoreItems(item)):
        logging.debug("You're holding too many of this item! Not putting up a buy order.")
        if myOrderActive:
            logging.debug("In fact you have a buy order up for this item! Deleting it.")
            deleteOrder(myOrderID)
        return
    
    if (closedAvgMetric >= 25 and priceRange >= 10) or priceRange >= 20:
        if myOrderActive:
            if (myPlatPrice != (postPrice)):
                logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
                updateListing(myOrderID, str(postPrice), 1, str(visibility))
                return
            else:
                logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
                return
        else:
            postOrder(itemID, orderType, str(postPrice), str(1), True, modRank)
            logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
            return
    elif myOrderActive:
        logging.debug(f"Not a good time to have an order up on this item. Deleted {orderType} order for {myPlatPrice}")
        logging.debug(f"Current highest buyer is:{bestBuyer['platinum']}")
        deleteOrder(myOrderID)
        return


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

    #probably don't want to be looking at this item right now if there's literally nobody interested in selling it.
    avgCost = (inventory["purchasePrice"] * inventory["number"]).sum() / inventory["number"].sum()
    logging.debug(item, avgCost)
    if numSellers == 0:
        postPrice = int(avgCost+30)
        if myOrderActive:
            updateDBPrice(item, postPrice)
            updateListing(myOrderID, postPrice, 1, str(visibility))
            return
        else:
            postOrder(itemID, orderType, postPrice, str(1), str(True), modRank)
            updateDBPrice(item, postPrice)
            return
    bestSeller = liveSellerDF.iloc[0]
    closedAvgMetric = bestSeller["platinum"] - itemStats["closedAvg"]
    postPrice = bestSeller['platinum'] - 1
    inventory = inventory[inventory.get("name") == item].reset_index()
    

    if bestSeller["platinum"] - avgCost <= 0:
        SelfTexting.send_push("EMERGENCY", f"The price of {item} is probably dropping and you should sell this to minimize losses asap")

    if avgCost + 10 > postPrice and numSellers >= 2:
        postPrice = max([avgCost + 10, liveSellerDF.iloc[1]['platinum']-1])
    else:
        postPrice = max([avgCost + 10, postPrice])
        
    if myOrderActive:
        if (myPlatPrice != (postPrice)):
            logging.debug(f"AUTOMATICALLY UPDATED {orderType.upper()} ORDER FROM {myPlatPrice} TO {postPrice}")
            updateDBPrice(item, int(postPrice))
            updateListing(myOrderID, str(int(postPrice)), 1, str(visibility))
            return
        
        else:
            updateDBPrice(item, int(myPlatPrice))
            logging.debug(f"Your current (possibly hidden) posting on this item for {myPlatPrice} plat is a good one. Recommend to make visible.")
            return
    else:
        response = postOrder(itemID, orderType, int(postPrice), str(1), str(True), modRank)
        updateDBPrice(item, int(postPrice))
        logging.debug(f"AUTOMATICALLY POSTED VISIBLE {orderType.upper()} ORDER FOR {postPrice}")
        return

    


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
    orderDF = orderDF[orderDF.get("username") != config.inGameName].reset_index().drop("index", axis=1)
    #display(orderDF)
    numTraders = orderDF.shape[0]
    #if no online buyers/sellers
    logging.debug(f"Week average {closedMetricKey}:\t{itemStats[closedMetricKey]}")
    if numTraders == 0 and myOrderActive == False:
        #send_push("No buyers active", f"There is no one {orderType}ing {item}. Log in and decide what to do yourself.")
        postOrder(itemID, orderType, 1, 1, True, modRank)
        logging.debug(f"No {orderType}ers for this item!")
    else:
        bestTrader = orderDF.loc[0]

        #Measures the price gap between the current best trader and the best price that item has ever been posted at in the past week.
        #Ex. if the best sell price seen on a Primed Continuity over the past week was 70, and the current best trader is selling for 80, this would be 10.
        #If this Metric is high, a posting should not be made in that category, since it represents an especially good person to contact.
        liveOrderMetric = metricMult * (bestTrader["platinum"] - itemStats[liveMetricKey])

        #Measures the gap between the best reported closed price on an item and the best trader. For example, if the lowest an item was closed at was for
        #80 platinum and the highest buy order is listed at 60, this would be 20 which represents a good time to overcut that individual.
        #This metric is probably very easily tricked by market manipulation of people either marking items as being sold for absurdly high or absurdly low.
        closedOrderMetric = metricMult * (itemStats[closedMetricKey] - bestTrader["platinum"])

        #Thie measures the gap between the average closed price and the price of the best trader. For example, if an item goes for 50 plat on average and
        #the best buyer is buying for 30, it may also be a good time to overcut them.
        closedAvgMetric = metricMult * (itemStats["closedAvg"] - bestTrader["platinum"])

        postPrice = bestTrader['platinum']+metricMult

        if orderType == "buy":
                
            if ((inventory[inventory["name"] == item]["number"].sum() > 1) and (closedAvgMetric < (15 + 5 * inventory[inventory["name"] == item]["number"].sum())) or ignoreItems(item)):
                logging.debug("You're holding too many of this item! Not putting up a buy order.")
                if myOrderActive:
                    logging.debug("In fact you have a buy order up for this item! Deleting it.")
                    deleteOrder(myOrderID)
                return
            
            if closedAvgMetric > 15:
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
        buySellOverlap = buySellOverlap[(buySellOverlap.get("priceShift") >= config.priceShiftThreshold) | (buySellOverlap.index.isin(inventory["name"].unique()))]
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

            compareLiveOrdersWhenBuying(item, liveOrderDF, itemStats, currentOrders, itemID, modRank, inventory)
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
    raise Exception(f"Unexpected {err=}, {type(err)=}")

config.setConfigStatus("runningLiveScraper", False)