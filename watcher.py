import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from update_DB import update_DB, trigger_copy, trigger_ceres, trigger_folder




class Watcher:

    DIRECTORY_TO_WATCH = os.environ['DIRECTORY_TO_WATCH']

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        print '-------------   WATCHING: '+self.DIRECTORY_TO_WATCH
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print "Error"

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):

        print '!!!!!!!!!!!!!!!!!!!!!!!!!!\n'

        print 'EVENT:   ',event

        print '!!!!!!!!!!!!!!!!!!!!!!!!!!\n'

        if event.event_type == 'created':
            print "FOLDER event received created event - %s" % event.src_path
            
            trigger_copy(event.src_path)
            #time.sleep(60)
            #update_DB()
            #time.sleep(30)
            #trigger_ceres()


if __name__ == '__main__':

    w = Watcher()
    w.run()










