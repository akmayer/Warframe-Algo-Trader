import json
conf = open("config.json")
configData = json.load(conf)
conf.close()

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

notif_platform = configData["notif_platform"]
pb_token = configData["pushbutton_token"]
pushbutton_device_iden = configData["pushbutton_device_iden"]
pushover_user_token = configData["pushover_user_token"]
pushover_application_token = configData["pushover_application_token"]
jwt_token = configData["wfm_jwt_token"]
jwt_token = "JWT " + jwt_token.split(" ")[-1]
inGameName = configData['inGameName']
platform = configData['platform'].lower()
webhookLink = configData["webhookLink"]
# Read JSON file
with open('settings.json') as settings:
    data = json.load(settings)

# Extract values and initialize variables
blacklistedItems = data['blacklistedItems']
whitelistedItems = data['whitelistedItems']
strictWhitelist = data['strictWhitelist']
priceShiftThreshold = data['priceShiftThreshold']
avgPriceCap = data['avgPriceCap']
maxTotalPlatCap = data['maxTotalPlatCap']
volumeThreshold = data['volumeThreshold']
rangeThreshold = data['rangeThreshold']
pingOnNotif = data["pingOnNotif"]