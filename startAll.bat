pushd %~dp0
start cmd.exe /k "uvicorn inventoryApi:app --reload"
cd my-app
start cmd.exe /k "npm run dev"