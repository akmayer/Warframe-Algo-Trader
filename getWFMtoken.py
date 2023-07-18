import json
import requests
import config

WFM_API = "https://api.warframe.market/v1"

def login(
    user_email: str, user_password: str, platform: str = "pc", language: str = "en"
):
    """
    Used for logging into warframe.market via the API.
    Returns (User_Name, JWT_Token) on success,
    or returns (None, None) if unsuccessful.
    """
    headers = {
        "Content-Type": "application/json; utf-8",
        "Accept": "application/json",
        "Authorization": "JWT",
        "platform": platform,
        "language": language,
    }
    content = {"email": user_email, "password": user_password, "auth_type": "header"}
    response = requests.post(f"{WFM_API}/auth/signin", data=json.dumps(content), headers=headers)
    if response.status_code != 200:
        return None, None
    return (response.json()["payload"]["user"]["ingame_name"], response.headers["Authorization"])

# UNCOMMENT LINE BELOW IF YOU'RE ON PC:
# MAKE SURE TO FILL IN <YOUR_INFO> BLANKS WITH YOUR INFO
# print(login("<YOUR_WF.M_EMAIL>", "<YOUR_WF.M_PASSWORD>"))
#
# IF YOU'RE ON A NON-PC PLATFORM UNCOMMENT THIS LINE BELOW AND REPLACE THE <YOUR_PLATFORM> WITH WHATEVER PLATFORM YOU'RE ON
# "pc" for pc, "ps4" for ps4, "xbox" for xbox, "switch" for switch
# print(login("<YOUR_WF.M_EMAIL>", "<YOUR_WF.M_PASSWORD>", "<YOUR_PLATFORM>"))