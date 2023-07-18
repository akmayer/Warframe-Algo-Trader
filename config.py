import json
f = open("config.json")
configData = json.load(f)
f.close()

def getConfigStatus(key):
    f = open("config.json")
    configData = json.load(f)
    f.close()
    return configData[key]

def setConfigStatus(key, value):
    f = open("config.json")
    configData = json.load(f)
    f.close()
    configData[key] = value
    with open("config.json", "w") as outfile:
        outfile.write(json.dumps(configData, indent=4))
    return


pb_token = configData["pushbutton_token"]
pushbutton_device_iden = configData["pushbutton_device_iden"]
jwt_token = configData["wfm_jwt_token"]
inGameName = configData['inGameName']
platform = configData['platform']
# Read JSON file
with open('settings.json') as file:
    data = json.load(file)

# Extract values and initialize variables
blacklistedItems = data['blacklistedItems']
priceShiftThreshold = data['priceShfitThreshold']
avgPriceCap = data['avgPriceCap']
volumeThreshold = data['volumeThreshold']
rangeThreshold = data['rangeThreshold']
