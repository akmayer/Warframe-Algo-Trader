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

# Configure logging format and level
logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)

# Get the Tesseract OCR executable path
user_home = os.path.expanduser("~")
user_tesseract_path = os.path.join(user_home, r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
fallback_tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Set the Tesseract path based on availability
if os.path.exists(user_tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = user_tesseract_path
else:
    pytesseract.pytesseract.tesseract_cmd = fallback_tesseract_path

# Function to count alphanumeric characters in a string
def countAlphanumeric(s):
    s = s.replace("\n", "")
    numbers = sum(c.isdigit() for c in s)
    letters = sum(c.isalpha() for c in s)
    spaces = sum(c.isspace() for c in s)
    return numbers + letters + spaces

# Function to remove a template from an image
def removeTemplate(postProcessImage, postProcessTemplate):
    w, h = postProcessTemplate.shape
    res = cv2.matchTemplate(postProcessImage, postProcessTemplate, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)
    for pt in zip(*loc[::-1]):  # Switch columns and rows
        cv2.rectangle(postProcessImage, pt, (pt[0] + w, pt[1] + h), (255, 255, 255), -1)
    return postProcessImage

# Function to preprocess an image
def preProcess(pngPath):
    image = cv2.imread(pngPath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

# Function to extract data from an image using Tesseract OCR
def extractData(cv2PilImage):
    text = pytesseract.image_to_data(cv2PilImage, output_type='data.frame')
    text = text[text.conf != -1]
    text.head()
    return text

# Function to extract text from an image using Tesseract OCR
def extractText(cv2PilImage):
    text = pytesseract.image_to_string(cv2PilImage, lang='eng', config='--psm 6')
    return text

# Function to display an image (utilized for debugging)
def displayImg(cv2PilImage):
    img = np.asarray(cv2PilImage)
    imgplot = plt.imshow(img)

# Configuration
textInterval = 20
timeAtLastText = time.time() - textInterval
confidence = 0.9

# Preprocess images for template matching
windowsPost = preProcess("WindowsLogo.png")
arrowPost = preProcess("WhisperArrow.png")

while config.getConfigStatus("runningWarframeScreenDetect"):
    try:
        # Check if the ChatMinimize.png icon is on the screen with a certain confidence level
        if pyautogui.locateOnScreen('ChatMinimize.png', confidence=confidence) is not None:
            # Get the coordinates of the ChatMinimize.png icon
            searchIconLoc = pyautogui.locateCenterOnScreen('ChatMinimize.png', confidence=confidence)
            
            # Capture the region around the ChatMinimize icon (whisper bar)
            whisperBar = pyautogui.screenshot("whispers.png", region=(searchIconLoc.x - 1080, searchIconLoc.y - 27, 1053, 54))
            whisperPost = preProcess("whispers.png")
            
            # Remove templates (Windows logo and arrow) from the whisper bar image
            removeTemplate(whisperPost, windowsPost)
            removeTemplate(whisperPost, arrowPost)

            # Extract data from the processed image
            data = extractData(whisperPost)
            if data.shape[0] > 0:
                s = data.iloc[0].loc["text"]
            else:
                s = ""

            # Count alphanumeric characters in the extracted text
            alphaCount = countAlphanumeric(s)

            # Check conditions to send a push notification
            if alphaCount >= 4 and (time.time() - timeAtLastText) > textInterval and pyautogui.locateOnScreen('ChatMinimize.png', confidence=confidence) is not None:
                timeAtLastText = time.time()
                print(f"Trade from {s}")
                SelfTexting.send_push("WFTrade", f"Whisper(s) from {s}")
    except AttributeError:
        # Ignore any attribute errors that might occur
        pass

    # Wait for a short time before repeating the loop
    time.sleep(0.5)
    logging.debug("LOOKING FOR WARFRAME")

# Set the status of runningWarframeScreenDetect to False when the loop ends
config.setConfigStatus("runningWarframeScreenDetect", False)
