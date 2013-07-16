import argparse
import Queue
import os
import time
from datetime import datetime
from engine import Engine 
"""
Adding a whole directory to a queue
Then getting from the queue and indexing until the queue is empty
This is the rate at which the indexing should happen even if 

- Run on 10.60 to get comparable results to previous runs

- Using monitored_directory and index_directory2
"""


parser = argparse.ArgumentParser(description="the index directory")
parser.add_argument("index_directory", help="the index_directory to refresh")
parser.add_argument("monitored_directory", help="the monitored_directory to load into queue")



args = parser.parse_args()
index_directory = args.index_directory
monitored_directory = args.monitored_directory
search_engine = Engine(index_directory)
buffered_writer = search_engine.writer(120, 1000, 512)

queue = Queue.Queue()
path = monitored_directory

def recursive_put(path, queue):

	if os.path.isfile(path):
		queue.put(path)

	elif os.path.isdir(path):
		ls = os.listdir(path)
		for l in ls:
			recursive_put(os.path.join(path, l), queue)
	else: 
		pass

recursive_put(path, queue)

print "files are loaded"
print "beginning the indexing part"

counter = 0
while not queue.empty():

	queue_time0 = time.time()
	path = queue.get()
	queue_time1 = time.time()

	index_time0 = time.time()
	search_engine.add_document(path, buffered_writer)
	index_time1 = time.time()

	queue_time = queue_time1 - queue_time0
	index_time = index_time1 - index_time0

	counter += 1

	if counter % 500 == 0:

		print "indexed path, queue_time, index_time, path: ", [str(datetime.now()), queue_time, index_time, path]

