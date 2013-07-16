import argparse
import Queue
import os
import time
from datetime import datetime
from engine import Engine 


parser = argparse.ArgumentParser(description="the index directory")
parser.add_argument("index_directory", help="the index_directory to refresh")
parser.add_argument("monitored_directory", help="the monitored_directory to load into queue")


args = parser.parse_args()
index_directory = args.index_directory
monitored_directory = args.monitored_directory
print "hey what's up?"
search_engine = Engine(index_directory)

total_time = search_engine.re_index(monitored_directory)

print "total time taken: ", total_time