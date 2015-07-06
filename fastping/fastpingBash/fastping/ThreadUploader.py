#!/usr/bin/env python

import logging
from PingListener import PingListener
import threading
from UploaderOPT import UploaderOPT


class ThreadUploader (threading.Thread):
    #id, name, sharedVariable, lock
    def __init__(self, threadID, name, event,shared):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.shared=shared
        self.upload=UploaderOPT()        
        logging.basicConfig(filename='fastPing.log',level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
        self.event=event
       
   
    def run(self):
        self.upload.initialize(self.shared,self.shared.uploaderCondition)
        self.shared.check_killed("Uploader",self.event)     
        if self.shared.parameters.Upload:
            print "Starting " + self.name
            while not self.shared.finishCycle:                 
                self.upload.state_process()
                self.shared.check_killed("Uploader",self.event)     
        print "Uploader: Finished"    
        
  
