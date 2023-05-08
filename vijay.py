import os
import boto3
import re
import time
import pymsteams
import sys

# List of target services
#target_services = ["crud", "rc"]

#sys.stdout.flush()
# Get the list of arguments passed to the script
target_services = sys.argv[1:]
print(targets_services)

while True:
    with open('test.log', 'a') as f:
        f.write(f"Current time: {time.time()}\n")
    time.sleep(1)

