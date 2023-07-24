# Warframe Algorithmic Trading

![image](https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/4602f014-a7df-40e9-b504-390a528d95a1)

<img src="https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/965c21ca-73f8-47f3-abcb-cb896e1f939c" height="512">

## Motivation

Warframe blends free-to-play mechanics with a premium currency system that is essential to smooth player progression. Players can acquire this premium currency, platinum, either through in-game purchases or by engaging in a dynamic player-driven economy, where they can trade their virtual possessions with other players. To facilitate these trades and foster a thriving marketplace, platforms such as Warframe.market have emerged, revolutionizing the way players make trades. By using the information on this platform, this program aims to add liquidity to the market, delivering better value to both buyers and sellers.To achieve this, my program provides methods of algorithmically determining high interest items based on real-time market data, automatic postings to warframe.market, and an interactive frontend to control and track your inventory as you are playing. Additionally, it uses optical character recognition (OCR) to notice in-game events and give quick phone notifications when trading opportinies arise. Many players with active, seemingly promising, postings on warframe.market are afk in-game and difficult to reach. This program aims to reduce the impact that those users have on the website by both often providing better deals than those users and giving the user quick notifications to their own trades to encourage quick responses. The components involved are:

- FastAPI: FastAPI is used in this program to create the backend API that handles the logic for determining high-interest items based on real-time market data, managing inventory, and automatically making postings to warframe.market.
- React: React is utilized to develop the interactive frontend that allows players to control and track their inventory as they play the game with dynamic UI components.
- Tailwind CSS: Tailwind CSS is used to style the user interface, providing a pleasing and clear aesthetic for use.
- SQLite3 Databases: SQLite3 is used to store and track the player's inventory and transactions.
- Pytesseract: Pytesseract is used to perform optical character recognition on the player's screen, allowing it to recognize in-game events related to trading opportunities. When such opportunities arise, the program can send quick phone notifications to the player.
- Pushbullet: Pushbullet is used for their friendly push notification api to send notifications to my phone. Note that you need pushbutton installed on your phone for this and there is more setting up of credentials.

Additionally, this [video](https://youtu.be/5g3vUm-XlyE) contains a summary of how this method remains profitable for the user along with a link to a discord server where you can discuss this program with me.

<img src=https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/ef79875f-bfbb-435a-a248-e78d738ef059 width="495" height="270">


## How To Use

### Initialization

You can currently build this programs two ways. The recommended way is through Docker which will be 2 lines in a cmd prompt, creating a containerized version of the app that's simple to run. The other way is through manually installing the depenencies on your pc and running it from the source code.

#### Method A. Docker:

> A limitation of running this project with Docker is that you will be unable to utilize OCR for detecting when you've received an in-game message.

##### A. Requirements:

- [Docker](https://docs.docker.com/get-docker/)

#### A. Steps:

1. Initialize the configuration files by running `docker run --rm -v ".:/app" -w /app python:3.11-slim-bookworm python3 init.py` on Windows or `docker run --rm -v "$(pwd):/app" --user $(id -u):$(id -u) -w /app python:3.11-slim-bookworm python3 init.py` if you're on linux. If this fails on windows because you are not in the docker-users group, see [this](https://stackoverflow.com/questions/61530874/docker-how-do-i-add-myself-to-the-docker-users-group-on-windows) stack overflow post.
2. Continue straight to [Setup](https://github.com/akmayer/Warframe-Algo-Trader/tree/main#setup)

#### Method B. From source:

> IF YOU'RE COMPLETELY UNFAMILIAR WITH THE COMMAND LINE AND PYTHON, CHECK OUT THIS GUIDE FIRST: https://rentry.co/wfmalgotraderbasic2
> (To be honest the guide is very well written I would recommend checking it out anyway)

##### B. Requirements:

- Python 3.11. Some earlier versions of Python 3 do not like some of the newer syntax I used in the API, so make sure you have the latest version of Python.
- Node.js for frontend and to use npm ([link](https://nodejs.org/en/download))
- Pushbullet (Only necessary for any phone notifications)
- ~~Tesseract-OCR (Only necessary for real time phone notifications [link](https://github.com/UB-Mannheim/tesseract/wiki))~~ (Tesseract Deprecated, moved to EE.log. Files still remain as proof of how cool it was)

##### B. Steps:

> Note: The following steps are executed through the command line for installation from source.

1. `cd` to the project directory, which will be `Warframe-Algo-Trader` if you downloaded with a git clone, and `Warframe-Algo-Trader-main` if you downloaded from a zip file.
2. Run `pip install -r requirements.txt`.
3. Run `pip install uvicorn`.
4. `cd my-app` then run `npm install` to download the necessary packages. If this fails, first install npm then run it.
5. `cd ../` to return to the top level of the project.
6. Run `python init.py` to initialize the tables and config.json file which will store credentials to access various api's.

### Setup

> Note: These steps are not executed from the command line, you will need to open these json files with a text editor.

1. After you have initialized the project, paste your in game name into the `config.json` file with the key, "inGameName".
2. Paste your platform into the `config.json` file with the key, "platform".
3. Get your jwt token to access your warframe.market account with their api. To do this, see this [guide](https://github.com/NKN1396/warframe.market-api-example).

**The JWT token is structured like "JWT eraydsfhalefibnzsdlfi". It includes the letters, "JWT" as well as a space before all the seemingly random characters.**


**Steps below are only required for pushbullet mobile notifications:**

4. ~~Install Tesseract-OCR from [their github](https://github.com/UB-Mannheim/tesseract/wiki). Either of the default installation paths should be fine but it should either end up in `C:Program Files\Tesseract-OCR` or in your `~\AppData\Local\Programs\Tesseract-OCR` where `~` is your user home directory.~~
5. Install pushbullet on your phone. Additionally, on the Pushbullet website, login and add your phone as a device.
6. After adding your phone as a device, make sure you are in the "Devices" tab. Then, on the website, click your phone to open the push chats with it.
7. Clicking your phone will change the url to `https://www.pushbullet.com/#devices/<DEVICE_TOKEN>`. Copy this token and paste it into your config.json file with the key, "pushbullet_device_iden".
8. Under the settings tab, click Create Access Token. Copy that token and paste it into your config.json file with the key, "pushbullet_token".

### Running

#### Method A) Docker

Running `docker compose up --build` will start two containers, one for the python app, running on port `8000` and the other running the web UI, running on port `3000`.

![image](https://user-images.githubusercontent.com/23193271/254992499-82d408e6-0a4f-4dcf-909b-f95d31e268a6.png)

#### Method B) From source

If you are on windows, you can navigate to the top level of the project and run `startAll.bat`. The application is a locally hosted website at 127.0.0.1:3000, which you can open in a browser. If you want to see the api, that's hosted at 127.0.0.1:8000.

If you are not on windows, then in the top level, run `uvicorn inventoryApi:app --reload` to run the api. In a new terminal window, navigate into the `my-app` directory then run `npm run dev` to run the website. The addresses will be the same.

**Always keep in mind that if someone messages you with the warframe.market copy-paste message in game, you are bound by the wf.m TOS to go through with it. They may message you with a slightly worse price (for you) than is currently listed, possibly because the program detected that you could raise or lower your price, but the person did not refresh their page seeing the new price. According to 1.5 on the warframe.market TOS, you must honor the price they came to you with.** However, this program will always place your prices close to the current best buy and sell prices, so if someone approaches you with a number absurdly different from one of those, it may be worth disputing.

### Transaction Control

![image](https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/e5b2c27a-28ae-4f81-887c-978fe3ef36ff)

The first button, that will start out looking like "Stats Reader Status: Not running" starts to gather 7 days of data on every item on warframe.market. This takes about 2 minutes to run. **You NEED to let this run to completion before the rest of the program will work fully.**

The second button uses that data to determine which items seem "interesting". Then, it will delete all the buy and sell orders on your account to replace with its suggested ones. It will go through the interesting items and put "buy" posts on warframe.market at a higher price than any one else, **if** it decide's it's a good time to do so based on the currnt live postings. You may have a lot of "buy" posts up so ensure that you have enough platinum to honor people's messages to you. If you're technically inclined and know some python, you can fidget with the parameters in `LiveScraper.py` which can provide flexibility about which items you personally find interesting, or limit the number of total buy requests you can put up at once. The program will also put up "sell" orders automatically based on your inventory, but strictly higher than what you bought that item for on average, to ensure that the user is not at a loss by running this program. Leave this button on running in the background while you have trades available and have warframe open to be able to trade.

The third button ~~combines pyautogui with OCR to detect when you receive whispers and send a notification to your phone when you do. Leave this on at the same time as the second button if you plan on doing other things while you let the whispers come to you and the notifactions let you respond quickly.~~ checks the EE.log for new whispers appearing and notifies your phone based on that

Skip to [Inventory Manager](https://github.com/akmayer/Warframe-Algo-Trader/tree/main#inventory-manager), ignore the rest of this note about ocr below.

**A note about OCR and phone notifications:**

You **_must_** set your in-game chat scale to 200 and your chat text size to LARGE for this to work. Additionally, you must extend your in game chat box as far horizontally as you can. If you playing on a 1920x1200 screen, this should be enough. When you are waiting for people to message you about trades, your screen should look like this:

![image](https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/89555782-ffc5-4a3a-83c1-4b36cee3fe66)

If you are NOT on a 1920x1200 screen, click the Start button next to Screen Reader Status: Not running for a few seconds. Then alt-tab into warframe for a few seconds so that the program can detect where it thinks your whisper notifications are. Ideally, the whispers.png file should look like this:

![image](https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/1549006a-5035-4617-82ea-e6419b02e6d6)

which includes the arrow on the left but does not include the chat-minimizing icon on the right.

If it does not look like this, you may have to fidget with values in line 74 of `AutoScanWaframe.py`.

**Another note:**

If you have an Android then Pushbullet may not vibrate on notification which can be inconvenient. There are other 3rd party apps for android like Macrodroid which can solve this.

### Inventory Manager

![image](https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/b6391dc5-e5ce-4ba2-8fbb-9d5553a560c2)

When someone approaches you trying to sell an item to you, type its name in the Purchase New Item: section and the Price you bought it at, then click Buy. It will automatically be added to your inventory. If the Live Updater is running, then when it gets around to that item, it will automatically post a "sell" order on warframe.market for higher than your average purchase price on that item. When someone approaches you trying to buy that item off of you based on your posting, type the price into the textbox next to the "Sell" button in the row corresponding with that item and hit "Sell". If that was the last one of that item in your inventory, it will immediately delete your sell order on warframe.market so that you don't have a fake listing.

### Visualizations

![image](https://github.com/akmayer/Warframe-Algo-Trader/assets/11152158/5e851eba-eec7-44be-b4f5-97bb7d44b07d)

To see the transactions logged by this app, simply click "Load Graph" with no inputs and it will show everything in the log. This estimates your account value by exactly calculating your net platinum profit after each trade, and adding that to an estimation of how much your inventory is worth based on the prices you bought your items at. (Intuitively when you buy something, you aren't poorer, the money is just in held in your asset). Both the startDate and endDate parameters are optional, and adding only one will leave the other one uncapped.
