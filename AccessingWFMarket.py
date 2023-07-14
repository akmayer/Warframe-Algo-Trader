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
            "platform": "pc",
            "language": "en",
            "Authorization": self.jwt_token,
        }
        self.lastRequestTime = 0
        self.timeBetweenRequests = 2

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

def getItemId(url_name):
    allItemsLink = "https://api.warframe.market/v1/items"
    r = requests.get(allItemsLink)
    itemList = r.json()["payload"]["items"]
    allItemDF = pd.DataFrame.from_dict(itemList)
    return allItemDF[allItemDF.get("url_name") == url_name].reset_index().loc[0, "id"]

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
        "item": item,
        "order_type": order_type,
        "platinum": platinum,
        "quantity": quantity,
        "visible": visible
    }
    if modRank:
        json_data["rank"] = modRank

    
    
    response = warframeApi.post('https://api.warframe.market/v1/profile/orders', json=json_data)

    if response.status_code == 200:
        f = open("tradeLog.txt", "a")
        f.write(f"POSTED - item: {itemName} - order_type : {order_type} - platinum : {platinum} - visible : {visible}\n")
        f.close()

    return response
    

def deleteOrder(orderID):
    warframeApi.delete(f'https://api.warframe.market/v1/profile/orders/{orderID}')
    
def getOrders():
    html_doc = warframeApi.get("https://warframe.market/profile/Yelbuzz").text
    soup = BeautifulSoup(html_doc, 'html.parser')
    return json.loads(soup.find("script", {"id": "application-state"}).getText())["payload"]

def updateListing(listing_id, platinum, quantity, visibility, itemName, order_type):
    try:
        url = WFM_API + "/profile/orders/" + listing_id
        contents = {
            "platinum": platinum,
            "quantity": quantity,
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