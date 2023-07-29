# Importing required modules
from fastapi import FastAPI, status, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
import csv
import sqlite3
import sys
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime
import config
import uvicorn
import logging
import json
import subprocess
import io
from fastapi.responses import StreamingResponse

# Loading configuration data from "config.json" file
f = open("config.json")
configData = json.load(f)
f.close()
jwt_token = configData["wfm_jwt_token"]

# Create FastAPI app
app = FastAPI()

# Configure CORS middleware to allow requests from all origins
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic models for request and response bodies
class Item(BaseModel):
    name: str
    purchasePrice: float | None = None
    listedPrice: int | None = None
    number: int | None = None

class Transact(BaseModel):
    name: str
    transaction_type: str
    price: float | None = None

# Function to handle system signal
def receive_signal(signalNumber, frame):
    print('Received:', signalNumber)
    sys.exit()

# Function to aggregate and delete rows by name in the inventory database
def aggregate_and_delete_rows_by_name(name):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(number), SUM(number * purchasePrice) FROM inventory WHERE name = ?", (name,))
    result = cursor.fetchone()
    total_number = result[0]
    weighted_average = result[1] / total_number if total_number else 0

    cursor.execute("DELETE FROM inventory WHERE name = ? AND rowid NOT IN (SELECT MIN(rowid) FROM inventory WHERE name = ?)", (name, name))

    cursor.execute("UPDATE inventory SET number = ?, purchasePrice = ? WHERE name = ?", (total_number, weighted_average, name))

    conn.commit()

    cursor.close()
    conn.close()

    return total_number, weighted_average

# Initialize process variables for scrapers
liveScraperProcess = None
statisticsScraperProcess = None
screenReaderProcess = None

# Event to be executed on app startup
@app.on_event("startup")
async def startup_event():
    import signal
    signal.signal(signal.SIGINT, receive_signal)
    logger = logging.getLogger("uvicorn.access")

    config.setConfigStatus("runningWarframeScreenDetect", False)
    config.setConfigStatus("runningLiveScraper", False)
    config.setConfigStatus("runningStatisticsScraper", False)

# Test endpoint for logging
@app.get("/testlog")
async def testLog():
    logging.debug("Testing debug.")
    logging.info("Testing info.")
    logging.warning("Testing warning! Check console!")
    logging.error("Testing error.")
    logging.info(f"Config testVar {config.testVar}.")
    return {}

# Root endpoint
@app.get("/")
async def root():
    return {"Nothing Here!": True}

# Endpoint to get a list of names of all tradable items
@app.get("/all_items")
async def get_a_list_of_names_of_all_tradable_items():
    allItemsLink = "https://api.warframe.market/v1/items"
    r = requests.get(allItemsLink)
    itemList = r.json()["payload"]["items"]
    itemNameList = [x["url_name"] for x in itemList]
    return {"item_names": itemNameList}

# Endpoint to get all items from the inventory
@app.get("/items")
async def getItems():
    jsonArray = []
    con = sqlite3.connect("inventory.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute(f"SELECT id, name, purchasePrice, listedPrice, number FROM inventory ")
    for row in res:
        jsonArray.append(dict(row))
    con.close()
    return jsonArray

# Endpoint to get the sum of total purchase price and total listed price of all items in the inventory
@app.get("/items/sum")
async def sumItems():
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    cur.execute("SELECT SUM(number * purchasePrice) AS total_purchase_price, SUM(number * listedPrice) AS total_listed_price FROM inventory")
    result = cur.fetchone()
    con.close()
    return {"total_purchase_price": result[0], "total_listed_price": result[1]}

# Endpoint to add an item to the inventory
@app.post("/item")
async def addItem(item: Item):
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    alreadyExists = cur.execute(f"SELECT COUNT(name) FROM inventory WHERE name='{item.name}'").fetchone()
    if alreadyExists[0] != 0:
        cur.execute("INSERT INTO inventory (name, purchasePrice, number) VALUES(?,?,?)", [item.name, item.purchasePrice, item.number])
        con.commit()
        con.close()
        aggregate_and_delete_rows_by_name(item.name)
        return {"Executed": True}
    if item.name and item.purchasePrice and item.number:
        cur.execute("INSERT INTO inventory (name, purchasePrice, number) VALUES(?,?,?)", [item.name, item.purchasePrice, item.number])
        con.commit()
        con.close()
        return {"Executed": True}
    else:
        con.close()
        return {"Executed": False, "Reason": "Need a purchase price and number."}

# Endpoint to remove an item from the inventory
@app.delete("/item")
async def removeItem(item: Item):
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    alreadyExists = cur.execute(f"SELECT COUNT(name) FROM inventory WHERE name='{item.name}'").fetchone()
    if alreadyExists[0] != 0:
        cur.execute(f"DELETE FROM inventory WHERE name='{item.name}'")
        con.commit()
        con.close()
        return {"Executed": True}
    else:
        con.close()
        return {"Executed": False, "Reason": "Item not in database."}

# Endpoint to update an item in the inventory
@app.put("/item")
async def updateItem(item: Item):
    if item.number == 0:
        await removeItem(item)
        return {"Executed": True}
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    alreadyExists = cur.execute(f"SELECT COUNT(name) FROM inventory WHERE name='{item.name}'").fetchone()
    if alreadyExists[0] != 0:
        if item.name and item.purchasePrice:
            cur.execute(f"UPDATE inventory SET purchasePrice=?, number=?, listedPrice=? WHERE name=?", [item.purchasePrice, item.number, item.listedPrice, item.name])
            con.commit()
            con.close()
            return {"Executed": True}
        else:
            con.close()
            return {"Executed": False, "Reason": "Need a purchaseprice and number."}
    else:
        con.close()
        return {"Executed": False, "Reason": "Item not in database."}

# Endpoint to sell an item from the inventory
@app.post("/item/sell")
async def sellItem(item: Item):
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    alreadyExists = cur.execute(f"SELECT COUNT(name) FROM inventory WHERE name='{item.name}'").fetchone()
    if alreadyExists[0] != 0:
        cur.execute("UPDATE inventory SET number=number-1 WHERE name=?", [item.name])
        con.commit()
        numLeft = cur.execute(f"SELECT SUM(number) FROM inventory WHERE name='{item.name}'").fetchone()[0]
        con.close()
        if numLeft == 0:
            await removeItem(item)
            return {"Executed": True}
        return {"Executed": numLeft}
    else:
        con.close()
        return {"Executed": False, "Reason": "Item not in database."}

# Function to get the order ID for a given item from warframe.market API
def get_order_id(item_name: str):
    url = f"https://api.warframe.market/v1/profile/{config.inGameName}/orders"

    headers = {
        "Content-Type": "application/json; utf-8",
        "Accept": "application/json",
        "auth_type": "header",
        "platform": config.platform,
        "language": "en",
        "Authorization": jwt_token
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        sell_orders = data["payload"]["sell_orders"]

        for order in sell_orders:
            if order["item"]["url_name"] == item_name:
                return order["id"]

        return None

    return None

# Endpoint to delete an order from warframe.market API
@app.put("/market/{item_name}")
def delete_order(item_name: str):
    con = sqlite3.connect("inventory.db")
    cur = con.cursor()
    numLeft = cur.execute(f"SELECT SUM(number) FROM inventory WHERE name='{item_name}'").fetchone()[0]
    con.close()
    if numLeft != 1:
        return {"message": "Not deleting order since you have may of these left"}

    order_id = get_order_id(item_name)

    if order_id is None:
        return {"message": "Order not found"}

    delete_url = f"https://api.warframe.market/v1/profile/orders/{order_id}"

    headers = {
        "Content-Type": "application/json; utf-8",
        "Accept": "application/json",
        "auth_type": "header",
        "platform": config.platform,
        "language": "en",
        "Authorization": jwt_token,
    }

    response = requests.delete(delete_url, headers=headers)

    if response.status_code == 200:
        return {"message": "Order deleted successfully"}
    else:
        raise HTTPException(
            status_code=400,
            detail=f'Something went wrong accessing wf.market api.',
        )

# Endpoint to get all transactions from the transactions table
@app.get("/transactions")
async def get_transactions():
    jsonArray = []
    con = sqlite3.connect("inventory.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            datetime TEXT,
            transactionType TEXT,
            price INTEGER
        ) STRICT
    """)
    res = cur.execute(f"SELECT id, name, datetime, transactionType, price from transactions ")
    for row in res:
        jsonArray.append(dict(row))
    con.close()
    return jsonArray

# Endpoint to create a transaction and insert it into the transactions table
@app.post("/transaction")
def create_transaction(t: Transact):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            datetime TEXT,
            transactionType TEXT,
            price INTEGER
        ) STRICT
    """)

    cursor.execute("INSERT INTO transactions (name, datetime, transactionType, price) VALUES (?, ?, ?, ?)",
                   (t.name, datetime.now(), t.transaction_type, t.price))

    conn.commit()
    conn.close()

    return {"message": "Transaction created successfully"}

# Endpoint to get the status of the live scraper
@app.get("/live_scraper")
def get_live_scraper_status():
    return {"Running": config.getConfigStatus("runningLiveScraper")}

# Endpoint to start the live scraper
@app.post("/live_scraper/start")
def start_live_scraper():
    global liveScraperProcess
    if config.getConfigStatus("runningLiveScraper"):
        return {"Executed": False, "Reason": "Scraper already running"}
    else:
        liveScraperProcess = subprocess.Popen(["python", "LiveScraper.py"])
        config.setConfigStatus("runningLiveScraper", True)
        f = open("tradeLog.txt", "w")
        f.write(f"Starting log file at {datetime.now()}\n")
        f.close()
        return {"Executed": True}

# Endpoint to stop the live scraper
@app.post("/live_scraper/stop")
def stop_live_scraper():
    global liveScraperProcess
    if liveScraperProcess is None:
        return {"Executed": False, "Reason": "Scraper was not running."}
    config.setConfigStatus("runningLiveScraper", False)
    liveScraperProcess.wait()
    return {"Executed": True}

# Endpoint to get the status of the statistics scraper
@app.get("/stats_scraper")
def get_stats_scraper_status():
    return {"Running": config.getConfigStatus("runningStatisticsScraper")}

# Endpoint to start the statistics scraper
@app.post("/stats_scraper/start")
def start_stats_scraper():
    global statisticsScraperProcess
    if config.getConfigStatus("runningStatisticsScraper"):
        return {"Executed": False, "Reason": "Scraper already running"}
    else:
        statisticsScraperProcess = subprocess.Popen(["python", "StatsScraper.py"])
        config.setConfigStatus("runningStatisticsScraper", True)
        return {"Executed": True}

# Endpoint to stop the statistics scraper
@app.post("/stats_scraper/stop")
def stop_stats_scraper():
    global statisticsScraperProcess
    if statisticsScraperProcess is None:
        return {"Executed": False, "Reason": "Scraper was not running."}
    config.setConfigStatus("runningStatisticsScraper", False)
    statisticsScraperProcess.wait()
    return {"Executed": True}

# Endpoint to get the status of the screen reader
@app.get("/screen_reader")
def get_screen_reader_status():
    return {"Running": config.getConfigStatus("runningWarframeScreenDetect")}

# Endpoint to start the screen reader
@app.post("/screen_reader/start")
def start_screen_reader():
    global screenReaderProcess
    if config.getConfigStatus("runningWarframeScreenDetect"):
        return {"Executed": False, "Reason": "Scraper already running"}
    else:
        config.setConfigStatus("runningWarframeScreenDetect", True)
        screenReaderProcess = subprocess.Popen(["python", "EEParser.py"])
        return {"Executed": True}

# Endpoint to stop the screen reader
@app.post("/screen_reader/stop")
def stop_screen_reader():
    global screenReaderProcess
    if screenReaderProcess is None:
        return {"Executed": False, "Reason": "Screen reader was not running."}
    config.setConfigStatus("runningWarframeScreenDetect", False)
    screenReaderProcess.wait()
    return {"Executed": True}

# Endpoint to generate and return a graph
@app.get("/graph")
def write_graph_to_file(startDate: str | None = None, endDate: str | None = None):
    if startDate is None or startDate == "":
        startDate = "1990"
    if endDate is None or endDate == "":
        endDate = "3000"
    imgGen = subprocess.run(["python", "GenerateProfitFigure.py", startDate, endDate])
    with open("accValue.png", "rb") as f:
        image_data = f.read()

    buffer = io.BytesIO(image_data)

    return StreamingResponse(buffer, media_type="image/png")
