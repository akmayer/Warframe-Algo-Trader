import json
import requests
from bs4 import BeautifulSoup
import time
import config
import pandas as pd
import customLogger

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
            'User-Agent': 'Warframe Algo Trader/1.3.1',
        }
        self.lastRequestTime = 0
        self.timeBetweenRequests = 3

    def waitUntilDelayEnds(self):
        if (time.time() - self.lastRequestTime) < self.timeBetweenRequests:
            time.sleep(self.lastRequestTime - time.time() + self.timeBetweenRequests)
        
    def get(self, link, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        self.lastRequestTime = time.time()
        r = requests.get(link, headers=self.headers)
        #print(time.time()-t0)
        return r
    def post(self, link, json, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        self.lastRequestTime = time.time()
        r = requests.post(link, headers=self.headers, json=json)
        #print(time.time()-t0)
        return r
    def delete(self, link, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        self.lastRequestTime = time.time()
        r = requests.delete(link, headers=self.headers)
        #print(time.time()-t0)
        return r
    def put(self, link, json, headers=None):
        t0 = time.time()
        self.waitUntilDelayEnds()
        self.lastRequestTime = time.time()
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
    customLogger.writeTo(
        "wfmAPICalls.log",
        f"POST:{WFM_API}/auth/signin\tResponse:{response.status_code}"
    )
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

    customLogger.writeTo(
        "wfmAPICalls.log",
        f"POST:{WFM_API}/profile/orders\tResponse:{response.status_code}\tItem:{itemName}\tOrder Type:{order_type}\tPlatinum:{platinum}\tQuantity:{quantity}\tVisible:{visible}"
    )

    if response.status_code == 200:
        customLogger.writeTo(
            "orderTracker.log",
            f"POSTED\tItem:{itemName}\tOrder Type:{order_type}\tPlatinum:{platinum}\tQuantity:{quantity}\tVisible:{visible}"
        )

    return response
    

def deleteOrder(orderID):
    r = warframeApi.delete(f'{WFM_API}/profile/orders/{orderID}')
    customLogger.writeTo(
        "wfmAPICalls.log",
        f"DELETE:{WFM_API}/profile/orders/{orderID}\tResponse:{r.status_code}"
    )
    if r.status_code == 200:
        customLogger.writeTo(
            "orderTracker.log",
            f"DELETED\tOrder ID: {orderID}"
        )
    
def getOrders():
    r = warframeApi.get(f"{WFM_API}/profile/{config.inGameName}/orders")
    customLogger.writeTo(
        "wfmAPICalls.log",
        f"GET:{WFM_API}/profile/{config.inGameName}/orders\tResponse:{r.status_code}"
    )
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
        customLogger.writeTo(
            "wfmAPICalls.log",
            f"PUT:{WFM_API}/profile/orders/{listing_id}\tResponse:{response.status_code}\tItem:{itemName}\tOrder Type:{order_type}\tPlatinum:{platinum}\tVisible:{visibility}"
        )  
        response.raise_for_status()  # Raises an exception for non-2xx status codes
        if response.status_code == 200:
            customLogger.writeTo(
                "orderTracker.log",
                f"UPDATED\tItem:{itemName}\tOrder Type:{order_type}\tPlatinum:{platinum}\tVisible:{visibility}"
            )
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
