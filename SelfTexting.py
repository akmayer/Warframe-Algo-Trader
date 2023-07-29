import requests
import time
import config

def send_push(title, message):
    # Set the headers required for the Pushbullet API request
    headers = {
        'Access-Token': config.pb_token,  # Access token from the config module
        'Content-Type': 'application/json',  # Request content type
    }

    # Prepare the data to be sent as JSON
    json_data = {
        'body': message,  # Message content
        'title': title,  # Message title
        'type': 'note',  # Type of push notification (note)
        'device_iden': config.pushbutton_device_iden  # Device identifier from the config module
    }

    # Send the push notification using the Pushbullet API
    response = requests.post('https://api.pushbullet.com/v2/pushes', headers=headers, json=json_data)


# The following code will execute only if this script is run directly (not imported as a module)
if __name__ == "__main__" and '__file__' not in globals():
    # Add a delay of 10 seconds to ensure the script has time to initialize
    time.sleep(10)
    
    # Call the send_push function with sample title and message
    send_push("test", "test config")
