from fileMonitorQueueLogged import MonitorThread, IndexerThread
import Queue
from engine import Engine
import shutil
import os
import settings


def start():

	f = open(settings.MONITOR_LOG, 'w')
	f.close()
	print "monitor log created"

	f = open(settings.INDEXER_LOG, 'w')
	f.close()
	print "indexer log created"

	search_engine = Engine(settings.INDEX_DIR)
	print "index_directory refreshed"
	queue = Queue.Queue() # the common queue
	monitor_thread = MonitorThread(queue, settings.MONITORED_DIR, settings.MONITOR_LOG_RATE, settings.MONITOR_LOG)
	indexer_thread = IndexerThread(queue, settings.INDEX_DIR, settings.INDEXER_LOG_RATE, settings.INDEXER_LOG)
	monitor_thread.start()
	#print "monitor thread started"
	#search_engine.re_index(settings.MONITORED_DIR) # reindexing the monitor_directory from scratch
	#print "monitor_directory re_indexed"
	indexer_thread.start()
	print "indexer thread started"

if __name__ == '__main__':
	start()












