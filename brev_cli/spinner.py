#!/usr/bin/env python

import itertools
import sys
import time
import threading
import platform

class Spinner(object):


    spinner_cycle = [
        " [🥞   ]",
        " [ 🥞  ]",
        " [  🥞 ]",
        " [   🥞]",
        " [  🥞 ]",
        " [ 🥞  ]",
        " [🥞   ]",
    ] if platform.system() == "Darwin" else itertools.cycle(['-', '/', '|', '\\'])
    i = 0

    def __init__(self):
        self.emojiSupported = platform.system() == "Darwin"
        self.stop_running = threading.Event()
        self.spin_thread = threading.Thread(target=self.init_spin)

    def start(self):
        # self.stop()
        self.spin_thread.start()

    def stop(self):
        try:
            self.stop_running.set()
            self.spin_thread.join()
        except:
            pass

    def init_spin(self):
        while not self.stop_running.is_set():
            # sys.stdout.write(self.spinner_cycle.next()) # .next() deprecated in python3 apparently 
            if self.emojiSupported:
                # sys.stdout.write(self.spinner_cycle[self.i % len(self.spinner_cycle)] + "\r")#, end="\r")
                print(self.spinner_cycle[self.i % len(self.spinner_cycle)] , end="\r")
                time.sleep(.1)
                self.i += 1
            else:                
            # last working code below
                sys.stdout.write(next(self.spinner_cycle))
                sys.stdout.flush()
                time.sleep(0.25)
                sys.stdout.write('\b')