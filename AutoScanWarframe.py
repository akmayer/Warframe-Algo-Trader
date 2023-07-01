import cv2
import pytesseract
import pyautogui
import time
import numpy as np
import matplotlib.pyplot as plt
import SelfTexting
import config
import logging
import os

logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)

# Get the current user's home directory
user_home = os.path.expanduser("~")

# Construct the user-specific path to the Tesseract OCR executable
user_tesseract_path = os.path.join(user_home, r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe")

# Construct the fallback path to the Tesseract OCR executable
fallback_tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Set the Tesseract path
if os.path.exists(user_tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = user_tesseract_path
else:
    pytesseract.pytesseract.tesseract_cmd = fallback_tesseract_path

def countAlphanumeric(s):
    s = s.replace("\n","")
    numbers = sum(c.isdigit() for c in s)
    letters = sum(c.isalpha() for c in s)
    spaces  = sum(c.isspace() for c in s)
    return numbers+letters+spaces

def removeTemplate(postProcessImage, postProcessTemplate):
    w, h = postProcessTemplate.shape

    res = cv2.matchTemplate(postProcessImage, postProcessTemplate, cv2.TM_CCOEFF_NORMED)
    threshold = .8
    loc = np.where(res >= threshold)
    for pt in zip(*loc[::-1]):  # Switch columns and rows
        cv2.rectangle(postProcessImage, pt, (pt[0] + w, pt[1] + h), (255, 255, 255), -1)
    
    return postProcessImage

def preProcess(pngPath):
    image = cv2.imread(pngPath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def extractData(cv2PilImage):
    text = pytesseract.image_to_data(cv2PilImage, output_type='data.frame')
    text = text[text.conf != -1]
    text.head()
    return text

def extractText(cv2PilImage):
    # Grayscale, Gaussian blur, Otsu's threshold
    # Perform text extraction
    text = pytesseract.image_to_string(cv2PilImage, lang='eng', config='--psm 6') 
    return text

def countAlphanumeric(s):
    s = s.replace("\n","")
    numbers = sum(c.isdigit() for c in s)
    letters = sum(c.isalpha() for c in s)
    spaces  = sum(c.isspace() for c in s)
    return numbers+letters+spaces

def displayImg(cv2PilImage):
    img = np.asarray(cv2PilImage)
    imgplot = plt.imshow(img)

textInterval = 20
timeAtLastText = time.time() - textInterval
confidence = 0.9

windowsPost = preProcess("WindowsLogo.png")
arrowPost = preProcess("WhisperArrow.png")

while config.getConfigStatus("runningWarframeScreenDetect"):
    try:
        if (pyautogui.locateOnScreen('ChatMinimize.png', confidence=confidence)) != None:
            searchIconLoc = pyautogui.locateCenterOnScreen('ChatMinimize.png', confidence=confidence)
            whisperBar = pyautogui.screenshot("whispers.png", region=(searchIconLoc.x - 1080,searchIconLoc.y - 27, 1053, 54))
            whisperPost = preProcess("whispers.png")
            removeTemplate(whisperPost, windowsPost)
            removeTemplate(whisperPost, arrowPost)

            #displayImg(whisperPost)

            data = extractData(whisperPost)
            if data.shape[0] > 0:
                s = data.iloc[0].loc["text"]
            else:
                s=""
            
            alphaCount = countAlphanumeric(s)

            
            if alphaCount >= 4 and (time.time() - timeAtLastText) > textInterval and ((pyautogui.locateOnScreen('ChatMinimize.png', confidence=confidence)) != None):
                timeAtLastText = time.time()
                print(f"Trade from {s}")
                SelfTexting.send_push("WFTrade", f"Whisper(s) from {s}")
    except AttributeError:
        pass

    time.sleep(0.5)
    logging.debug("LOOKING FOR WARFRAME")

config.setConfigStatus("runningWarframeScreenDetect", False)