import http.client
import urllib
import config
import requests
import time

def send_ios_push(app_name, message):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": config.pushover_application_token,
            "user": config.pushover_user_token,
            "message": message,
            "title": app_name
        }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()



def send_android_push(title, message):
    headers = {
        'Access-Token': config.pb_token,
        'Content-Type': 'application/json',
    }

    json_data = {
        'body': message,
        'title': title,
        'type': 'note',
        'device_iden' : config.pushbutton_device_iden
    }

    response = requests.post('https://api.pushbullet.com/v2/pushes', headers=headers, json=json_data)


def send_push(title, message):
    if config.notif_platform == "android":
        send_android_push(title, message)
    elif config.notif_platform == "ios":
        send_ios_push(title, message)
    else:
        print("Invalid platform specified")


if __name__ == "__main__" and '__file__' not in globals():
    time.sleep(10)
    send_android_push("test", "test config")