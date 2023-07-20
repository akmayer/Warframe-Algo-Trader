FROM python:3.11-slim-bookworm

WORKDIR /app

RUN \
    apt update && \
    apt install sqlite3

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python3", "-m" , "uvicorn", "inventoryApi:app", "--host", "0.0.0.0", "--reload"]