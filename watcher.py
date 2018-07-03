import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from astropy.time import Time
from math import floor
from astropy.io import fits as pf
import subprocess
import os, sys
import django
from update_DB import update_DB


nightfmt="%Y-%m-%d"
copy2root = os.environ['FEROS_DATA_PATH']
sys.path.append(os.environ['DJANGO_PROJECT_PATH'])
from django.apps import apps
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MPG2p2m.settings")
django.setup()

from FEROS.models import *


normal_obsmode = {  'HIERARCH ESO DET READ CLOCK'   : 'R 225Kps Low Gain',
                    'CDELT1'                        : 1,
                    'CDELT2'                        : 1, }

HIERARCH_ESO_TPL_NAME = [   'FEROS bias',
                            'FEROS flatfield',
                            'FEROS ThAr+Ne wavelength calibration',
                            'FEROS obs.object-cal',
                        ]


def trigger_folder(src_path):

    current_session = get_session().strftime(nightfmt)

    if current_session == src_path.split('/')[-1]:
        copy_path       = copy2root+get_session().strftime(nightfmt)+'/RAW/'
        if not os.path.exists(copy_path):
            os.makedirs(copy_path)
    else:

        print '---------------------------------------------------------------'
        print 'Session and Remote night folder are different !!!!'
        print get_session().strftime(nightfmt)
        print src_path.split('/')[-2]
        print '---------------------------------------------------------------'


def trigger_copy(src_path):

    current_session = get_session().strftime(nightfmt)
    if current_session == src_path.split('/')[-2]:

        filename        = src_path.split('/')[-1]
        copy_path       = copy2root+get_session().strftime(nightfmt)+'/RAW/'

        if not os.path.exists(copy_path):
            os.makedirs(copy_path)

        if filename.split('.')[0] == 'FEROS':

            hdr = pf.getheader(src_path)

            if normal_obsmode['HIERARCH ESO DET READ CLOCK'] == hdr['HIERARCH ESO DET READ CLOCK'] and \
                normal_obsmode['CDELT1'] == hdr['CDELT1'] and \
                normal_obsmode['CDELT2'] == hdr['CDELT2'] and \
                hdr['HIERARCH ESO TPL NAME'] in HIERARCH_ESO_TPL_NAME:

                cmd='rsync -avz %s %s' %(  src_path, copy_path )
                status = subprocess.call(cmd, shell=True)
        else:
            print 'NOT FEROS!!!!'

    else:

        print '---------------------------------------------------------------'
        print 'Session and Remote night folder are different !!!!'
        print get_session().strftime(nightfmt)
        print src_path.split('/')[-2]
        print '---------------------------------------------------------------'





class Watcher:

    DIRECTORY_TO_WATCH = os.environ['DIRECTORY_TO_WATCH']

    print 'WATCHING: '+DIRECTORY_TO_WATCH

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(60)
        except:
            self.observer.stop()
            print "Error"

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            trigger_folder(event.src_path)

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print "Received created event - %s" % event.src_path

            trigger_copy(event.src_path)
            update_DB()


if __name__ == '__main__':

    w = Watcher()
    w.run()










