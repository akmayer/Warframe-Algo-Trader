import requests
import time
import config

def send_push(title, message):
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


if __name__ == "__main__" and '__file__' not in globals():
    time.sleep(10)
    send_push("test", "test config")