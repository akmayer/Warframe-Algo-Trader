import json
import requests

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