import os
import re
import SelfTexting
import config
from time import sleep

import logging
logging.basicConfig(format='{levelname:7} {message}', style='{', level=logging.DEBUG)

class WarframeLogParser:
    def __init__(self, log_path):
        self.log_path = log_path

    def clean_username(self, username):
        # Function to clean up non-ASCII characters from the username
        return username.encode("ascii", "ignore").decode("ascii")

    def process_line(self, line):
        # Regular expression to find the username in a line containing a whisper message
        result = re.search(r'(F)(.*\S)( to index (?:[1-9]|[1-9]\d)$)', line)
        if result is not None:
            # Extract the username from the regular expression match
            username = self.clean_username(result.group(2))

            # Log the username using the logging module
            logging.debug(username)

            # Print the username (for debugging purposes)
            print(username)

            # Send a push notification with the username using the SelfTexting module
            SelfTexting.send_push("WFTrade", f"Whisper(s) from {username}")

    def follow_and_parse_log(self):
        with open(self.log_path, 'r', encoding='latin-1') as file:
            # Move the file pointer to the end of the file
            file.seek(0, os.SEEK_END)

            # Continuously read lines from the log file while the "runningWarframeScreenDetect" configuration is True
            while config.getConfigStatus("runningWarframeScreenDetect"):
                line = file.readline()
                if line:
                    # Process the line if it contains a whisper message
                    self.process_line(line)
                else:
                    # Sleep for a short duration if no new lines are available in the log file
                    sleep(0.1)

# Example usage:
if __name__ == "__main__":
    # Define the path to the log file
    appdata_path = '/appdata_warframe'
    log_path = os.path.join(appdata_path, 'EE.log')

    # Check if the log file exists in the specified path, otherwise use the default path
    if not os.path.exists(log_path):
        log_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Warframe', 'EE.log')

    # Log the log file path using the logging module
    logging.debug(log_path)

    # Create an instance of WarframeLogParser and start following and parsing the log
    parser = WarframeLogParser(log_path)
    parser.follow_and_parse_log()
