import json

# Load configuration data from "config.json"
with open("config.json") as f:
    configData = json.load(f)

# Function to get configuration status by key from "configData"
def getConfigStatus(key):
    with open("config.json") as f:
        configData = json.load(f)
    return configData[key]

# Function to set configuration status by key to "value" in "configData" and save it back to "config.json"
def setConfigStatus(key, value):
    with open("config.json") as f:
        configData = json.load(f)
    configData[key] = value
    with open("config.json", "w") as outfile:
        outfile.write(json.dumps(configData, indent=4))
    return

# Accessing specific configuration data from "configData"
pb_token = configData["pushbutton_token"]
pushbutton_device_iden = configData["pushbutton_device_iden"]
jwt_token = configData["wfm_jwt_token"]
jwt_token = "JWT " + jwt_token.split(" ")[-1]
inGameName = configData['inGameName']
platform = configData['platform'].lower()

# Load data from "settings.json"
with open('settings.json') as file:
    data = json.load(file)

# Extract values from "data" and initialize variables
blacklistedItems = data['blacklistedItems']
priceShiftThreshold = data['priceShiftThreshold']
avgPriceCap = data['avgPriceCap']
volumeThreshold = data['volumeThreshold']
rangeThreshold = data['rangeThreshold']
