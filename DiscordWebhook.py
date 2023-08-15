import requests
import config

def sendMessage(message):

    if config.pingOnNotif:
        r = requests.get(config.webhookLink)
        creatorID = r.json()["user"]["id"]
        msg = {
            "content" : f"<@{creatorID}>, {message}",
        }
    else:
        msg = {
            "content" : f"{message}",
        }
    
    r = requests.post(f"{config.webhookLink}", data=msg)

if __name__ == "__main__":
    sendMessage("Testing webhook!")