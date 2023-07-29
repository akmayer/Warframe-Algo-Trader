import json
import requests
from bs4 import BeautifulSoup
import time
import config
import pandas as pd

class WarframeApi:
    def __init__(self):
        self.t0 = time.time()
        self.jwt_token = config.jwt_token
        self.headers = {
            "Content-Type": "application/json; utf-8",
            "Accept": "application/json",
            "auth_type": "header",
            "platform": config.platform,
            "language": "en",
            "Authorization": self.jwt_token,
            'User-Agent': 'Warframe Algo Trader/1.2.2',
        }
        self.lastRequestTime = 0
        self.timeBetweenRequests = 3

    def waitUntilDelayEnds(self):
        if (time.time() - self.lastRequestTime) < self.timeBetweenRequests:
            time.sleep(time.time() - self.lastRequestTime)
        
    def get(self, link, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        r = requests.get(link, headers=self.headers)
        #print(time.time()-t0)
        return r
    def post(self, link, json, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        r = requests.post(link, headers=self.headers, json=json)
        #print(time.time()-t0)
        return r
    def delete(self, link, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        r = requests.delete(link, headers=self.headers)
        #print(time.time()-t0)
        return r
    def put(self, link, json, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        r = requests.put(link, headers=self.headers, json=json)
        #print(time.time()-t0)
        return r
        

WFM_API = "https://api.warframe.market/v1"

warframeApi = WarframeApi()

def login(
    user_email: str, user_password: str, platform: str = "pc", language: str = "en"
):
    """
    Used for logging into warframe.market via the API.
    Returns (User_Name, JWT_Token) on success,
    or returns (None, None) if unsuccessful.
    """
    content = {"email": user_email, "password": user_password, "auth_type": "header"}
    response = warframeApi.post(f"{WFM_API}/auth/signin", data=json.dumps(content))
    if response.status_code != 200:
        return None, None
    return (response.json()["payload"]["user"]["ingame_name"], response.headers["Authorization"])

def postOrder(item, order_type, platinum, quantity, visible, modRank, itemName):
    
    json_data = {
        "item": str(item),
        "order_type": str(order_type),
        "platinum": int(platinum),
        "quantity": int(quantity),
        "visible": visible
    }
    if modRank:
        json_data["rank"] = modRank

    
    
    response = warframeApi.post(f'{WFM_API}/profile/orders', json=json_data)

    if response.status_code == 200:
        f = open("tradeLog.txt", "a")
        f.write(f"POSTED - item: {itemName} - order_type : {order_type} - platinum : {platinum} - visible : {visible}\n")
        f.close()

    return response
    

def deleteOrder(orderID):
    warframeApi.delete(f'{WFM_API}/profile/orders/{orderID}')
    
def getOrders():
    r = warframeApi.get(f"{WFM_API}/profile/{config.inGameName}/orders")
    return r.json()["payload"]

def updateListing(listing_id, platinum, quantity, visibility, itemName, order_type):
    try:
        url = WFM_API + "/profile/orders/" + listing_id
        contents = {
            "platinum": int(platinum),
            "quantity": int(quantity),
            "visible": visibility
        }
        response = warframeApi.put(url, json=contents)
        response.raise_for_status()  # Raises an exception for non-2xx status codes
        if response.status_code == 200:
            f = open("tradeLog.txt", "a")
            f.write(f"POSTED - item: {itemName} - order_type : {order_type} - platinum : {platinum} - visible : {visibility}\n")
            f.close()
        return True
    except requests.exceptions.RequestException as e:
        print(f"update_listing: {e}")
        return False
    
if __name__ == "__main__":
    r = warframeApi.post(
        f'{WFM_API}/profile/orders',
        {
            "item": "5bc1ab93b919f200c18c10ef",
            "platinum": 1,
            "order_type": "buy",
            "quantity": 1,
            "rank": 1,
            "visible": False
        }
    )
    print(r.status_code)
