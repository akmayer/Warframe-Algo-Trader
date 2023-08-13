import os
from datetime import datetime
logDir = "logs"

def writeTo(logFileName, line):
    with open(os.path.join(logDir, logFileName), "a") as logFile:
        logFile.write(f"{datetime.today()}\t{line}\n")

def clearFile(logFileName):
    with open(os.path.join(logDir, logFileName), "w") as logFile:
        logFile.write("")


if __name__ == "__main__":
    writeTo("apiCalls.log", "Some logging")
    #clearFile("apiCalls.log")