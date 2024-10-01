pushd "%~dp0" || exit /B
start wt -w AlgoTrader --title "BackEnd" --tabColor #f2b78d uvicorn inventoryApi:app --reload
cd my-app
start wt -w AlgoTrader --title "FrontEnd" --tabColor #8df2ef "C:\Program Files\nodejs\node.exe" npm run dev
popd