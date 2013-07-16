"""
06/06/13

This file provides moethods to monitor a file system to report the removed, added, and modified filepaths of the file system.


First let's test the pyinotify...
PyInotify Events:

Event Name	Is an Event	Description
IN_ACCESS	Yes	file was accessed.
IN_ATTRIB	Yes	metadata changed.
IN_CLOSE_NOWRITE	Yes	unwrittable file was closed.
IN_CLOSE_WRITE	Yes	writtable file was closed.
IN_CREATE	Yes	file/dir was created in watched directory.
IN_DELETE	Yes	file/dir was deleted in watched directory.
IN_DELETE_SELF	Yes	watched item itself was deleted.
IN_DONT_FOLLOW	No	don't follow a symlink (lk 2.6.15).
IN_IGNORED	Yes	raised on watched item removing. Probably useless for you, prefer instead IN_DELETE*.
IN_ISDIR	No	event occurred against directory. It is always piggybacked to an event. The Event structure automatically provide this information (via .is_dir)
IN_MASK_ADD	No	to update a mask without overwriting the previous value (lk 2.6.14). Useful when updating a watch.
IN_MODIFY	Yes	file was modified.
IN_MOVE_SELF	Yes	watched item itself was moved, currently its full pathname destination can only be traced if its source directory and destination directory are both watched. Otherwise, the file is still being watched but you cannot rely anymore on the given path (.path)
IN_MOVED_FROM	Yes	file/dir in a watched dir was moved from X. Can trace the full move of an item when IN_MOVED_TO is available too, in this case if the moved item is itself watched, its path will be updated (see IN_MOVE_SELF).
IN_MOVED_TO	Yes	file/dir was moved to Y in a watched dir (see IN_MOVE_FROM).
IN_ONLYDIR	No	only watch the path if it is a directory (lk 2.6.15). Usable when calling .add_watch.
IN_OPEN	Yes	file was opened.
IN_Q_OVERFLOW	Yes	event queued overflowed. This event doesn't belongs to any particular watch.
IN_UNMOUNT	Yes	backing fs was unmounted. Notified to all watches located on this fs.

"""      
import sys
import argparse
import os
import threading
import Queue
import smtplib
import time
import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent
from engine import Engine
import pyinotify
from datetime import datetime


class EventHandler(pyinotify.ProcessEvent):

    def __init__(self, queue, log_rate, log_file):

        self.queue = queue
        self.log_rate = log_rate
        self.log_file = log_file
        self.log_count = 0
        self.moved_from = None
        self.moved_to = None


    """
    def process_IN_ACCESS(self, event):
        #print "ACCESS event:", event.pathname

    def process_IN_ATTRIB(self, event):
        #print "ATTRIB event:", event.pathname

    def process_IN_CLOSE_NOWRITE(self, event):
        #print "CLOSE_NOWRITE event:", event.pathname

    def process_IN_CLOSE_WRITE(self, event):
        #print "CLOSE_WRITE event:", event.pathname

    def process_IN_MODIFY(self, event):
        print "MODIFY event:", event.pathname

    def process_IN_OPEN(self, event):
        print "OPEN event:", event.pathname

    def process_IN_ATTRIB(self, event):
        print "metadata changed: ", event.pathname 

    def process_IN_MODIFY(self, event):
        print "modified event: ", event.pathname
    """

    def process_IN_CREATE(self, event):

        if os.path.isfile(event.pathname):
            self.queue.put_nowait((event.pathname, True))
            if self.log_count % self.log_rate == 0:
                log(self.log_file, ("added %s to queue to add: " % [event.pathname, str(datetime.now())]))
        else:
            
            log(self.log_file, ("the path %s added to fs is not file" % [event.pathname, str(datetime.now())]))

        self.log_count += 1

    def process_IN_DELETE(self, event):

        self.queue.put_nowait((event.pathname, False))

        if self.log_count % self.log_rate == 0:
            log(self.log_file, ("added %s to queue to delete: " % [event.pathname, str(datetime.now())]))
        self.log_count += 1

    def process_IN_MOVED_FROM(self, event):

        self.moved_from = event.pathname

    def process_IN_MOVED_TO(self, event):

        self.moved_to = event.pathname

        if not (self.moved_from == None or self.moved_to == None):
            self.rename_directory(self.moved_from, self.moved_to)

        self.moved_from = None
        self.moved_to = None

    def process_IN_Q_OVERFLOW(self, event):

        # The event queue overflowed:
        # currently emailing karthik@silanano if an event queue overflow occurs
        sender = 'kartuppuluri@gmail.com'
        receiver = 'karthik@silanano.com'
        message = " The file monitor crashed!"

        #credentials:
        username = 'kartuppuluri'
        password = 'nofearkfart'

        server = smtplib.SMTP("smtp.gmail.com:587")
        server.starttls()
        server.login(username, password)
        server.sendmail(sender, receiver, message)
        server.quit()

        print "event queue overflowed and email sent to karthik@silanano.com ", datetime.now()

    def rename_directory(self, old_directory, new_directory):

        old_directory = old_directory.split('/')
        old_dir = old_directory[-1]
        old_dir_index = len(old_directory) - 1 # it's the last one
        self.recursive_update(new_directory, old_dir_index, old_dir)

    def recursive_update(self, path, old_dir_index, old_dir):

        tok_path = path.split('/')
        if os.path.isfile(path):

            tok_path[old_dir_index] = old_dir
            for i in range(len(tok_path)):

                if i != (len(tok_path) - 1):
                    tok_path[i] = tok_path[i] + '/'

            oldpath = ''.join(tok_path)

            self.queue.put_nowait((oldpath, False))
            self.queue.put_nowait((path, True))


            if self.log_count % self.log_rate == 0:
                log(self.log_file, ("added %s oldpath that was renamed to queue to delete from index " % [oldpath, str(datetime.now())]))
                log(self.log_file, ("added %s newpath that was renamed to queue to add to index " % [path, str(datetime.now())]))
            self.log_count += 1



        elif os.path.isdir(path):

            ls = os.listdir(path)
            for i in ls:
                self.recursive_update(os.path.join(path,i), old_dir_index, old_dir)

        else:

            print "the path in recursive_update is neither of a file or a directory", [path, str(datetime.now())]


class MonitorThread(threading.Thread):

    def __init__(self, queue, watch_directory, log_rate, log_file):

        self.queue = queue
        wm = pyinotify.WatchManager()
        wm.add_watch(watch_directory, pyinotify.ALL_EVENTS, rec=True, auto_add=True)
        event_handler = EventHandler(queue, log_rate, log_file)
        self.notifier = pyinotify.Notifier(wm, event_handler)
        threading.Thread.__init__(self) # needed for thread to instantiated

    def run(self):

        self.notifier.loop()

class IndexerThread(threading.Thread):

    def __init__(self, queue, index_directory, log_rate, log_file):

        self.search_engine = Engine(index_directory)
        self.buffered_writer = self.search_engine.new_buffered_writer(120, 100 , 512)
        self.queue = queue
        self.log_count = 0
        self.log_rate = log_rate
        self.log_file = log_file
        threading.Thread.__init__(self) # needed for thread to be instantiated

  
    def run(self):

        while True:

            while not self.queue.empty():

                path, add_or_delete = self.queue.get_nowait()
                time_taken, successful = self.add_or_remove(path, add_or_delete)

                if successful: 
                    if self.log_count % self.log_rate == 0:
                        if add_or_delete:
                            log(self.log_file, ("time taken to index path: ", [time_taken, path, str(datetime.now())]))
                        else:
                            log(self.log_file, ("time taken to un-index path: ", [time_taken, path, str(datetime.now())]))
                else:
                    log(self.log_file,("index/ un-index of path was unsuccessful: ", [path, str(datetime.now())]))

                self.log_count += 1


    """
    This method indexes/ removes an index of 'path', and returns the time taken to do so. 
        params:
            - path: the path to index/ remove from index
            - add_or_delete: True for add/ False for delete
        return:
            - time_taken (0.0 if unsuccessful; i.e. directory, not file)
            - boolean of successful or not (whether file or directory)
    """
    def add_or_remove(self, path, add_or_delete):

        if os.path.isdir(path):
            return [0.0, False]

        t0 = time.time()
        
        if add_or_delete:
            self.search_engine.add_document(path, self.buffered_writer)
        else:
            self.search_engine.remove_document(path, self.buffered_writer)

        t1 = time.time()
        time_taken = t1 - t0

        return [time_taken, True]


"""
runs the monitoring through the monitor and the indexer threads
"""

def run_monitor(index_directory, monitor_directory):

    queue = Queue.Queue()

    monitor_thread = MonitorThread(queue, monitor_directory, 1)
    indexer_thread = IndexerThread(queue, index_directory, 1)

    monitor_thread.start()
    #indexer_thread.start()

def log(log_file, data):

    if os.path.exists(log_file):
        with open(log_file, 'a') as f:
            f.write(str(data))
    else:
        print "there is no log file at the specified location: ", log_file


def main():
    #format: python fileMonitory.py index_dir watch_dir is_fresh
    parser = argparse.ArgumentParser(description='Monitor and index a directory')
    parser.add_argument("index_directory", help="where to store the indeces for the files in file system")
    parser.add_argument("watch_directory", help="directory to monitor")
    args = parser.parse_args()
    index_directory = args.index_directory
    watch_directory = args.watch_directory
   
    run_monitor(index_directory, watch_directory)




if __name__ == '__main__':
    main()





