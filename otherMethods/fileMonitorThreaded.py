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
from engine_threaded.py import Engine
import pyinotify
from datetime import datetime

"""
Queue convention:
for adding operation:
(pathname, file_or_not, operation)
for deleting:
(pathname, operation)

where:
file_or_not:
    0 for file
    1 for dir
operation:
    0 for delete
    1 for add
    2 for rename
"""

class EventHandler(pyinotify.ProcessEvent):

    def __init__(self, queue, log_rate):

        self.queue = queue
        self.log_count = 0
        self.moved_from = None
        self.moved_to = None
        self.log_rate = log_rate

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

            self.queue.put_nowait((event.pathname, 0, 1))
            if self.log_count % self.log_rate == 0:
                print "added FILE %s to queue to add: " % [event.pathname, str(datetime.now())]

        else:
            
            self.queue.put_nowait((event.pathname, 1, 1))
            print "added DIR %s to queue to add: " % [event.pathname, str(datetime.now())]

        self.log_count += 1

    def process_IN_DELETE(self, event):

        if not os.path.exists(os.path.split(event.pathname)[0]):
            pass
        else:
            if '.' in os.path.split(event.pathname)[1]:
                self.queue.put_nowait((event.pathnam, 0, 0))
            else:
                self.queue.put_nowait((event.pathname, 1, 0))

        print "path to del: ", event.pathname

        self.log_count += 1

    def process_IN_MOVED_FROM(self, event):

        self.moved_from = event.pathname

    def process_IN_MOVED_TO(self, event):

        self.moved_to = event.pathname
        path_type = None

        if not (self.moved_from == None and self.moved_to == None):

            if not os.path.exists(os.path.split(self.moved_from)[0]):
                pass
            else:
                if os.path.isfile(self.moved_to):
                    self.queue.put_nowait(((self.moved_from, self.moved_to), 0, 2))
                else:
                    self.queue.put_nowait(((self.moved_from, self.moved_to), 1, 2))

        print "moved_from, moved_to: ", [str(datetime.now()), self.moved_from, self.moved_to]


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

    

class MonitorThread(threading.Thread):

    def __init__(self, queue, watch_directory, log_rate):

        self.queue = queue
        self.watch_directory = watch_directory
        wm = pyinotify.WatchManager()
        wm.add_watch(self.watch_directory, pyinotify.ALL_EVENTS)
        event_handler = EventHandler(queue, log_rate)
        self.notifier = pyinotify.Notifier(wm, event_handler)
        threading.Thread.__init__(self) # needed for thread to instantiated

    def run(self):

        self.notifier.loop()


class IndexerThread(threading.Thread):

    def __init__(self, queue, index_directory, current_dirs, log_rate):

        self.search_engine = Engine(index_directory)
        self.buffered_writer = self.search_engine.writer(120, 5000 , 512)
        self.queue = queue
        self.current_dirs = current_dirs
        self.log_count = 0
        self.log_rate = log_rate
        self.thread_pool = {}
        threading.Thread.__init__(self) # needed for thread to be instantiated


    def run(self):

        while True:

            while not self.queue.empty():

                job = self.queue.get_nowait()
                path = job[0]
                if job[2] == 0: # deleting
                    time_taken = self.delete(path, job[1])
                elif job[2] == 1: # adding
                    time_taken = self.add(path, job[1])
                else: # renaming
                    time_taken = self.rename(job[0], job[1])

                if log_count % log_rate == 0:
                    print "time taken: ", [str(datetime.now()), time_taken, job]
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
    def add(self, path, path_type):

        if path_type == 0: # this path is a filepath
            time_taken = self.search_engine.add_document(path, self.buffered_writer)
            return time_taken
        else:
            sub_dirs_added, time_taken = self.search_engine.add_dir(path)
            for sub in sub_dirs:
                thread = MonitorThread(self.queue, sub, self.log_rate)
                self.thread_pool[sub] = thread
                thread.start()
            return time_taken
        print "added path: ", path

    def delete(self, path, path_type):

        if path_type == 0: #this path is a filepath
            
            time_taken = self.search_engine.remove_document(path, self.buffered_writer)
            return time_taken

        if path_type == 1:
            sub_dirs_removed, time_taken = self.search_engine.remove_dir(path)
            for sub in sub_dirs:
                thread = self.thread_pool[sub]
                try:
                    thread.__Thread_stop()
                except:
                    print "Could Not terminate thread!!!", sub
                del self.thread_pool[sub]
        print "deleted path: ", path

    def rename(self, oldpath, newpath):

        sub_dirs, time_taken = self.search_engine.rename_directory(oldpath, newpath)
        for sub in sub_dirs:
            old_dir, new_dir = sub
            old_thread = self.thread_pool[old_dir]
            try:
                old_thread.__Thread_stop()
            except:
                print "Couldnt terminate thread! ", old_dir
            del self.thread_pool[old_dir]
            new_thread = MonitorThread(self.queue, new_dir, self.log_rate)
            self.thread_pool[new_dir] = new_thread
            new_thread.start()
        print "renamed dir: ", [str(datetime.now()), oldpath, newpath]


"""
runs the monitoring through the monitor and the indexer threads
"""

def run_monitor(index_directory, monitor_directory):

    queue = Queue.Queue()

    monitor_thread = MonitorThread(queue, monitor_directory, 1)
    indexer_thread = IndexerThread(queue, index_directory, 1)

    monitor_thread.start()
    indexer_thread.start()



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





