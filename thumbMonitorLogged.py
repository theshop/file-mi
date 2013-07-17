"""
06/06/13

This file provides methods to monitor a file system to report the removed, added, and modified filepaths of the file system.
That information is then used to generate thumbnails of pictures(as recognized by PIL-python image library) that have been added to the filesystem
Note: No thumbnail is deleted, that is taken care of by another module during periodical checks.

First let's test the pyinotify...
PyInotify Events:

"""      
import sys
import argparse
import os
import threading
import Image
import Queue
import smtplib
import time
import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent
import pyinotify
from thumbnailer import Thumber
from datetime import datetime


class EventHandler(pyinotify.ProcessEvent):

    def __init__(self, queue, log_rate, log_file):

        self.queue = queue
        self.log_rate = log_rate
        self.log_file = log_file
        self.log_count = 0

    def process_IN_CREATE(self, event):

        if os.path.isfile(event.pathname):
            try:
                print "in try block with path: ", event.pathname
                print "does path exist? ", os.path.exists(event.pathname)
                im = Image.open(event.pathname)
                print "opened image"
                self.queue.put_nowait(event.pathname)
                print "to-be-thumbed added to queue", event.pathname
                if self.log_count % self.log_rate == 0:
                    log(self.log_file, ("added %s to queue to add: " % [event.pathname, str(datetime.now())]))
            except IOError:
                print "An IO error was caught"

        else:
            log(self.log_file, ("the path %s added to fs is not file" % [event.pathname, str(datetime.now())]))

        self.log_count += 1

    def process_IN_MOVED_TO(self, event):

        if os.path.isfile(event.pathname):
            try:
                im = Image.open(event.pathname)
                self.queue.put_nowait(event.pathname)
                print "to-be-thumbed added to queue"

                if self.log_count % self.log_rate == 0:
                    log(self.log_file, ("added %s to queue to add: " % [event.pathname, str(datetime.now())]))
            except:
                pass

        elif os.path.isdir(event.pathname):
            self.queue.put_nowait(event.pathname, True)

        else:
            pass


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

    def __init__(self, queue, watch_directory, log_rate, log_file):

        self.queue = queue
        wm = pyinotify.WatchManager()
        wm.add_watch(watch_directory, pyinotify.ALL_EVENTS, rec=True, auto_add=True)
        event_handler = EventHandler(queue, log_rate, log_file)
        self.notifier = pyinotify.Notifier(wm, event_handler)
        threading.Thread.__init__(self) # needed for thread to instantiated

    def run(self):

        self.notifier.loop()

class ThumberThread(threading.Thread):

    def __init__(self, queue, thumbnail_dir, log_rate, log_file, thumb_size, extension):

        self.queue = queue
        self.thumber = Thumber(thumb_size[0], thumb_size[1], thumbnail_dir, extension)
        self.log_count = 0
        self.log_rate = log_rate
        self.log_file = log_file
        threading.Thread.__init__(self) # needed for thread to be instantiated
  
    def run(self):

        while True:

            while not self.queue.empty():

                job = self.queue.get_nowait()
                if len(job) == 1: # It is a file 
                    self.thumber.thumb(job)
                else:
                    self.thumber.thumb_dir(job[0])

                self.log()
                self.log_count += 1


    def log(self):

         if self.log_count % self.log_rate == 0:
            log(self.log_file, ("time taken to thumb path: ", [time_taken, path, str(datetime.now())]))

"""
runs the monitoring through the monitor and the indexer threads
"""

def run_monitor(thumbnail_dir, monitor_dir):

    queue = Queue.Queue()

    monitor_thread = MonitorThread(queue, monitor_dir, 1)
    thumber_thread = ThumberThread(queue, thumbnail_dir, 1)

    monitor_thread.start()
    thumber_thread.start()

def log(log_file, data):

    if os.path.exists(log_file):
        with open(log_file, 'a') as f:
            f.write(str(data))
    else:
        print "there is no log file at the specified location: ", log_file


def main():

    queue = Queue.Queue()
    thumber_thread = ThumberThread(queue, '/home/labuser/thumb_dir', 1, '/home/labuser/thumb_log.txt', (500, 500), '.jpg')
    monitor_thread = MonitorThread(queue, '/home/labuser/thumb_monitor', 1, '/home/labuser/monitor_log.txt') #ok
    thumber_thread.start()
    monitor_thread.start()

if __name__ == '__main__':
    main()





