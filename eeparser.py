import os
import re
import SelfTexting
from time import sleep

log_path = os.getenv('LOCALAPPDATA') + r'/Warframe/EE.log'


def follow(filename):
    """generator function that yields new lines in a file"""
    with open(filename, 'r', encoding='latin-1') as file:
        # file.seek(0, os.SEEK_END)  # Go to the end of the file, disabled for testing
        while True:
            while line := file.readline():
                # If a line is not empty yield it to the generator
                yield line
            # No more lines are in the file - wait for more input
            sleep(.1)


def parse_log(log):
    ee = follow(log)
    for line in ee:
        # 51718.699 Net [Info]: IRC out: WHOIS Toothless99 This is an example line out of the log file. This line
        # fits all our criteria, its gets called when you receive a new whisper from someone, the username is cleanly
        # formatted and this call doesn't get used for region/relay channels or anything but user whispers.
        result = re.search(r'(WHOIS )(.*)', line)
        if result is not None:
            # Encode and decode to clean up some garbage unicode that gets attached to the end of the username
            username = result.group(2).encode("ascii", "ignore").decode("ascii").replace('`', '')
            print(username)
            SelfTexting.send_push("WFTrade", f"Whisper(s) from {username}")


parse_log(log_path)
