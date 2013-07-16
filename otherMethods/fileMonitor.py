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
import smtplib
import time
import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent
from engine import Engine
import pyinotify


class MyEventHandler(pyinotify.ProcessEvent):

    def __init__(self, engine):
        self.engine = engine

        if sys.platform == "win32":
            # For windows:
            self.default_timer = time.clock
        else:
            self.default_timer = time.time

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

    """

    def process_IN_CREATE(self, event):

        # adding to the filesAdded.txt
        f = open("filesAdded.txt", "a")
        f.write(event.pathname + "\n")
        f.close()

        time_taken, successful = self.add_or_remove(event.pathname, True)

        if successful:
            print "time_taken to add path: ", [event.pathname, time_taken]
        else:
            print "unsuccessful, event.pathname is of a directory, will not be added to index", event.pathname

    def process_IN_DELETE(self, event):

        # adding to filesDeleted.txt
        f = open("filesDeleted.txt", "a")
        f.write(event.pathname + "\n")
        f.close()

        time_taken, successful = self.add_or_remove(event.pathname, False)

        if successful:
            print "time_taken to remove path: ", [event.pathname, time_taken]
        else:
            print "unsuccessful, event.pathname is of a directory will not be deleted from index: ", event.pathname


    def process_IN_MODIFY(self, event):

        print "modified event: ", event.pathname

    def process_IN_MOVED_FROM(self, event):

        self.moved_from = event.pathname

    def process_IN_MOVED_TO(self, event):

        self.moved_to = event.pathname

        if not (self.moved_from == None or self.moved_to == None):
            self.rename_directory(self.moved_from, self.moved_to)

        self.moved_from = None
        self.moved_to = None

    def process_IN_ATTRIB(self, event):

        print "metadata changed: ", event.pathname 

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
            time_taken_remove, successful_remove = self.add_or_remove(oldpath, False)
            time_taken_add, successful_add = self.add_or_remove(path, True)

            if successful_remove:
                print "time taken to remove from index: ", [oldpath, time_taken_remove]
            else:
                print "SOMETHING WRONG, NOT REMOVING THE OLDPATH, THINKS IT IS NOT A FILE"

            if successful_add:
                print "time taken to add to index: ", [path, time_taken_add]
            else:
                print "SOMETHING WRONG, NOT ADDING THE NEWPATH, THINKS IT IS NOT A FILE"

        elif os.path.isdir(path):

            print "path is dir: ", path
            ls = os.listdir(path)
            for i in ls:
                self.recursive_update(os.path.join(path,i), old_dir_index, old_dir)

        else:

            print "the path in recursive_update is neither of a file or a directory", path

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

        t0 = self.default_timer()
        writer = self.engine.writer()

        if add_or_delete:
            self.engine.add_document(path, writer)
        else:
            self.engine.remove_document(path, writer)

        writer.commit()
        t1 = self.default_timer()
        time_taken = t1 - t0

        return [time_taken, True]


def main():
    #format: python fileMonitory.py index_dir watch_dir is_fresh
    parser = argparse.ArgumentParser(description='Monitor and index a directory')
    parser.add_argument("index_directory", help="where to store the indeces for the files in file system")
    parser.add_argument("watch_directory", help="directory to monitor")
    parser.add_argument("is_fresh", help="re-index everything/ use the existing indeces for the FS", type=bool)
    args = parser.parse_args()
    index_directory = args.index_directory
    watch_directory = args.watch_directory
    is_fresh = args.is_fresh
   
    # watch manager
    wm = pyinotify.WatchManager()
    wm.add_watch(watch_directory, pyinotify.ALL_EVENTS, rec=True, auto_add=True)

    #engine for the handler: 
    if is_fresh:
        engine = Engine(index_directory)
    else:
        engine = Engine(index_directory)
    # event handler
    eventHandler = MyEventHandler(engine)

    # notifier
    notifier = pyinotify.Notifier(wm, eventHandler)
    notifier.loop()

if __name__ == '__main__':
    main()





