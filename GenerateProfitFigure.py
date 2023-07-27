import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import time
import sys

# Set a flag to ignore Loki Prime (if True) or include it (if False)
ignoreLokiPrime = False

# Set the ignoredSet based on the ignoreLokiPrime flag
if ignoreLokiPrime:
    ignoredSet = set(['loki_prime_set'])
else:
    ignoredSet = set([])

# Function to calculate the value of assets at a specific datetime (dt)
def getValueOfAssets(dt, ignoredSet):
    # Connect to the SQLite database
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Get distinct names from the transactions table where datetime is before or equal to dt
    cursor.execute("SELECT DISTINCT name FROM transactions WHERE datetime <= ?", (dt,))
    names = cursor.fetchall()
    
    value_of_assets = 0
    
    # Calculate the value of assets for each name
    for name in names:
        name = name[0]  # Extract the name from the tuple
        if name in ignoredSet:
            continue
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE name = ? AND transactionType = 'sell' AND datetime <= ?", (name, dt))
        sell_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*), avg(price) FROM transactions WHERE name = ? AND transactionType = 'buy' AND datetime <= ?", (name, dt))
        buy_count, avg_price = cursor.fetchone()
        num_owned = int(buy_count) - sell_count
        if avg_price and num_owned:
            value_of_assets += (avg_price - 0) * num_owned
        else:
            pass
    
    # Close the database connection
    conn.close()
    return value_of_assets


def getValueOfAssets2(dt, ignoredSet):
    # Connect to the SQLite database
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    # Retrieve aggregated data of name, net count, and average price for each name
    cursor.execute("""
        SELECT name, SUM(CASE WHEN transactionType = 'buy' THEN 1 ELSE -1 END), AVG(CASE WHEN transactionType = 'buy' THEN price ELSE NULL END)
        FROM transactions
        WHERE datetime <= ? AND transactionType IN ('buy', 'sell')
        GROUP BY name
        HAVING name NOT IN ({})
    """.format(','.join(['?'] * len(ignoredSet))), (dt,) + tuple(ignoredSet))
    rows = cursor.fetchall()

    value_of_assets = 0

    # Calculate the value of assets based on the retrieved data
    for name, num_owned, avg_price in rows:
        num_owned = int(num_owned)
        if avg_price and num_owned:
            value_of_assets += avg_price * num_owned

    # Close the database connection
    conn.close()
    return value_of_assets
    
def extractDate(datetimeString):
    # Extract only the date part from the datetime string
    return datetimeString.split(" ")[0]

def genLabels(dateTimeList):
    labels = []
    lastDay = ""
    for datetimeStr in dateTimeList:
        date = extractDate(datetimeStr)
        # Append the date to labels if it's a new day after the year 2021, otherwise append an empty string
        if lastDay != date and date > "2021":
            labels.append(date)
        else:
            labels.append("")
        lastDay = date
    return labels

def getInventoryValueOverTime(startDate, endDate):
    # Connect to the SQLite database
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Generate the placeholders for the elements in ignoredSet
    placeholders = ', '.join(['?' for _ in ignoredSet])
    
    # Construct the SQL query with the placeholders and date range
    query = f"SELECT id, datetime FROM transactions WHERE name NOT IN ({placeholders}) AND datetime BETWEEN ? AND ? ORDER BY datetime"
    
    # Create the parameter tuple by concatenating ignoredSet and date range
    params = tuple(ignoredSet) + (startDate, endDate)
    
    # Execute the query with the parameter tuple
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    timestamps = []
    valueOverTime = []
    
    # Calculate the value of assets over time for each transaction
    for row in rows:
        id, date = row
        timestamps.append(date)
        valueOverTime.append(getValueOfAssets2(date, ignoredSet))
    
    return timestamps, valueOverTime

def getNetEarningsOverTime(startDate, endDate):
    # Connect to the SQLite database
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Generate the placeholders for the elements in ignoredSet
    placeholders = ', '.join(['?' for _ in ignoredSet])
    
    # Construct the SQL query with the placeholders and date range
    query = f"SELECT id, name, datetime, price, transactionType FROM transactions WHERE name NOT IN ({placeholders}) AND datetime BETWEEN ? AND ? ORDER BY datetime"
    
    # Create the parameter tuple by concatenating ignoredSet and date range
    params = tuple(ignoredSet) + (startDate, endDate)
    
    # Execute the query with the parameter tuple
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    placeholders = ', '.join(['?' for _ in ignoredSet])
        
    # Construct the SQL query with the placeholders and date range
    query = f"SELECT SUM(CASE WHEN transactionType = 'buy' THEN -1 * price ELSE price END) FROM transactions WHERE name NOT IN ({placeholders}) AND datetime < ? ORDER BY datetime"

    # Create the parameter tuple by concatenating ignoredSet and date range
    params = tuple(ignoredSet) + (startDate,)

    # Execute the query with the parameter tuple
    cursor.execute(query, params)
    initial_net_earnings = cursor.fetchall()[0][0] or 0
    conn.close()
    
    # Initialize variables
    net_earnings = initial_net_earnings
    timestamps = []
    earnings = []
    
    # Calculate net earnings over time
    for row in rows:
        id, name, timestamp, price, transaction_type = row
        if transaction_type == 'buy':
            net_earnings -= price
        elif transaction_type == 'sell':
            net_earnings += price
        timestamps.append(timestamp)
        earnings.append(net_earnings)

    return timestamps, earnings

def getAccountValueFig(timestamps, inventoryValueOverTime, netEarnings):
    # Configure plot styles
    plt.rcParams['text.color'] = '#E5ECF4'
    plt.rcParams['axes.labelcolor'] = '#E5ECF4'
    plt.rcParams['axes.edgecolor'] = '#E5ECF4'
    plt.rcParams['xtick.color'] = '#E5ECF4'
    plt.rcParams['ytick.color'] = '#E5ECF4'
    
    plt.rcParams['figure.facecolor'] = '#0A090C'
    plt.rcParams['axes.facecolor'] = '#0A090C'
    
    # Prepare data for plotting
    x = timestamps
    y = np.array(netEarnings) + np.array(inventoryValueOverTime)
    labels = genLabels(timestamps)
    
    # Create the plot
    plt.plot(x, y, '#8A4FFF')
    plt.xticks(x, labels, rotation=45)
    plt.title("Account Value Over Time")
    plt.ylabel("Liquid Platinum + Estimated Inventory Value")
    plt.xlabel("Time")
    plt.xticks(rotation=45)
    fig = plt.gcf()
    fig.autofmt_xdate()
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_edgecolor('#E5ECF4')
    return fig

# Get start and end dates from command line arguments
startDate = sys.argv[1]
endDate = sys.argv[2]

print(startDate, endDate)

# Calculate inventory value over time and net earnings over time
t = time.time()
timestamps, inventoryValueOverTime = getInventoryValueOverTime(startDate, endDate)
t = time.time()
timestamps, netEarningsOverTime = getNetEarningsOverTime(startDate, endDate)
t = time.time()

# Generate and save the account value plot
fig = getAccountValueFig(timestamps, inventoryValueOverTime, netEarningsOverTime)
fig.savefig("accValue.png")
