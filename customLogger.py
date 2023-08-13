import os
from datetime import datetime
logDir = "logs"

def makeGitIgnore():
    with open(os.path.join(logDir, ".gitignore"), "w") as gitignore:
        gitignore.write("# Ignore everything in this directory\n*\n# Except this file\n!.gitignore")

def verifyLogDir():
    if os.path.exists(os.path.join(logDir, ".gitignore")):
        return
    if os.path.exists(logDir):
        makeGitIgnore()
        return
    os.mkdir(logDir)
    makeGitIgnore()
    

def writeTo(logFileName, line):
    verifyLogDir()
    with open(os.path.join(logDir, logFileName), "a") as logFile:
        logFile.write(f"{datetime.today()}\t{line}\n")

def clearFile(logFileName):
    verifyLogDir()
    with open(os.path.join(logDir, logFileName), "w") as logFile:
        logFile.write("")


if __name__ == "__main__":
    verifyLogDir()