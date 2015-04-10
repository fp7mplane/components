#!/usr/bin/env python

from PingManagerOPT import PingManagerOPT 
import threading,sys

class ThreadSender (threading.Thread):
    #id, name, sharedVariable, lock
    def __init__(self, threadID, name,event, shared):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.shared=shared
        self.ping=PingManagerOPT(shared)
        self.cond= 'ping'
        self.event=event

    
    def run(self):

        print "Starting " + self.name
        self.ping.initialize()
        self.shared.check_killed("Sender",self.event)    
        self.ping.state_socket()
        self.shared.check_killed("Sender",self.event)        
        while self.cond == 'ping' :
            if self.ping.MAX_CYCLE is not -1:
                print "ping: \t"+str(self.ping.cycle.countCycle)+"/"+str(self.ping.MAX_CYCLE)     
            else:
                print "ping: \t"+str(self.ping.cycle.countCycle)            
            self.ping.state_ping()
            print "saving:\t"+str(self.ping.cycle.countCycle)
            self.cond=self.ping.state_save()
            self.shared.check_killed("Sender",self.event)       
         
        self.ping.state_idle()        
        print "Sender: Finished"
