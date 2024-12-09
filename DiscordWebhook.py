import requests
import config
from logging import debug, basicConfig, DEBUG

basicConfig(format='{levelname:7} {message}', style='{', level=DEBUG)

def sendMessage(message):
    if config.webhookLink == "":
        return

    if config.pingOnNotif:

        # Discord API returns 204 No Content for POST Webhook. Moreover, it can use the username that you pass in the "body.username"
        # No need for additionally requesting Webhook info
        # https://discord.com/developers/docs/resources/webhook#execute-webhook

        msg = {
            "content": message
        }

        debug(msg)

        headers = {
            "Content-Type": "application/json"
        }

        r = requests.post(f"{config.webhookLink}", json=msg, headers=headers)

        if r.status_code == 204:
            debug("Message successfully created")

if __name__ == "__main__":
    debug("This is Discord Integration")
    