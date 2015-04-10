#/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# IMPORTS + LOGGING + CONST DEFINITION
#------------------------------------------------------------------------

import os, time, sys, logging, socket, csv, random, thread
from datetime                   import timedelta
from subprocess                 import Popen, PIPE

from PingCycleOPT          import PingCycleOPT
from DestList              import DestList
from Stats                 import Stats

NB_RETRY = 5

#------------------------------------------------------------------------
# SUPPORT FUNCTIONS
#------------------------------------------------------------------------

def get_hostname():
    "\brief    Get underlying machine hostname"
    return Popen(["uname", "-n"], stdout = PIPE).communicate()[0].strip()


#------------------------------------------------------------------------
# PING MANAGER (OPT) CLASS
#------------------------------------------------------------------------

class PingManagerOPT():

    def __init__(self, Shared):
        self.shared=Shared 
    #------------------------------------------------------------------------
    # STATE MACHINE
    #------------------------------------------------------------------------

    def initialize(self):
        
        self.hostname      = get_hostname()
        self.cycle         = None
        self.dests         = DestList()
        self.startCycle    = 0
     
        self.RAW_DIR       = self.shared.parameters.RAW_DIR
        self.STATS_DIR     = self.shared.parameters.STATS_DIR
        self.SAVE_RAW_TRACES = self.shared.parameters.SAVE_RW
       
    #----------------------------------------------------------------------------------------#
    #----> STATE 01 -> SOCKET_OPENING
    #----------------------------------------------------------------------------------------#
    def state_socket(self):
        self.dests.reset()
       
        # LOAD PARAMETERS
        self.parse_config()
        # SET HOSTNAME
        self.shared.hostname=self.hostname
       
 
        try:     
            log = logging.getLogger("agent.ping_manager.socket")
            # SOCKET OPENING
            try:
                icmp = socket.getprotobyname('icmp')
                self.shared.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW,icmp)
                
                log.info("Socket opened: %s" % self.shared.socket)
            except socket.error, (errno, msg):
                if errno == 1:
                    log.error("%s -> ICMP messages can only be sent from processes running as root." % msg)
                    
                else:
                    log.error("Too many failures, aborting API calls.")
                print "Socket error, for more information check the log."    
                #-------------------change with a function, we use the same in fastping.py-------------------            
                self.shared.sender.event.set() #killing:exception open socket
                self.shared.uploaderCondition.acquire()                                
                self.shared.uploaderCondition.notifyAll() #wake up thread blocked on wait               
                self.shared.uploaderCondition.release()
                
            # CREATE PING_CYCLE_OPT and LISTENER
            self.cycle = PingCycleOPT(self.shared, self.delta_M,self.ping_freq, self.shared.socket) #preload
           
			# START PING MEASUREMENT
            log.info("PingCycle created (agent_hostname: %s) - INTERVAL: %s" % (self.hostname, self.delta_M))
            
           
            # SYNCHRONIZATION
            #wait_time = random.randint(1,int(self.delta_M.seconds/3))                               # RANDOM WAIT
            #---------------------------AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
            wait_time=0 #manage wait time with the number of probe            
            log.info("PingCycle synchronization - SLEEP: %f s" % wait_time)
            
            if(self.shared.sender.event.wait(wait_time)): #Reentrant lock: if there is a set, it will unlock and it will return true
                return                
       
            # CREATE RAW_FILE
            r_file = None
            try:
                os.makedirs(self.RAW_DIR)
                log.info("Directory %s do not exists, created it." % self.RAW_DIR)
            except OSError, (errno, msg):
                if errno != 17:
                    log.error("%s" % msg)
                    sys.exit(1)
            
            self.startCycle = time.time()
            
            if self.SAVE_RAW_TRACES:
                filename = str(self.hostname)+"_"+str(int(self.startCycle))+".rw"
                r_file = open(os.path.join(self.RAW_DIR,filename),'w')
                r_file.write("#ID\tTARGET_IP\tSEQ_N\tCYCLE\tRTT\tTIME_RECEIVED\tTIME_SENT\n")
            
            try:
                os.makedirs(self.STATS_DIR)
                log.info("Directory %s do not exists, created it." % self.STATS_DIR)
            except OSError, (errno, msg):
                if errno != 17:
                    log.error("%s" % msg)
                    self.shared.sender.event.set() #killing:exception
           
            self.cycle.countCycle += 1    
            
            # CREATE STATS REFERENCES   
            self.shared.stats = Stats(self.shared.destList,self.cycle.nDests,self.startCycle,self.cycle.countCycle,self.shared.parameters)  
            
            self.shared.receiver.receive.set_stats(self.shared.stats,r_file)
        except Exception, e:
            log.error("%s " % e)
            self.shared.sender.event.set() #killing:exception open socket
            
       
        log.info("State 01 finished")
        return "ping"
    #------------------------------------------------------------------------
    # ++ STATE 02 -> PING
    #------------------------------------------------------------------------

    def state_ping(self):
        
        log = logging.getLogger("agent.ping_manager.ping")
        
        try:
            log.info("Starting ping cycle %d." % self.cycle.countCycle)       
            self.cycle.run()
        except Exception, e:
            log.error("%s" % e)
        log.info("State 02 finished")  
        return "save"       # start pinging        
        

    #------------------------------------------------------------------------
    # ++ STATE 03 -> SAVE
    #------------------------------------------------------------------------
    
    def state_save(self):
        log = logging.getLogger("agent.ping_manager.save")
        if self.MAX_CYCLE == -1 or self.cycle.countCycle < self.MAX_CYCLE:
            self.startCycle = time.time()
            self.cycle.countCycle += 1    
             
            # CREATE NEW RAW FILE
            r_file = None
            if self.SAVE_RAW_TRACES == True:
                filename = str(self.hostname)+"_"+str(int(self.startCycle))+".rw"
                r_file = open(os.path.join(self.RAW_DIR,filename),'w')
                r_file.write("#ID\tTARGET_IP\tSEQ_N\tCYCLE\tRTT\tTIME_RECEIVED\tTIME_SENT\n")
            
            # CREATE STATS REFERENCES 
            self.shared.stats = Stats(self.shared.destList,self.cycle.nDests,self.startCycle,self.cycle.countCycle,self.shared.parameters)
           
          
            #<-------------------------------------------------------------------------> SAVE STATS
            self.shared.receiver.receive.set_stats(self.shared.stats,r_file)
            

            log.info("State 03 finished") 
            return "ping"       # start new ping_cycle
        
        else:
            log.info("State 03 finished") 
            return "idle"       # stop pinging
        
  
    #------------------------------------------------------------------------
    # ++ STATE 04 -> IDLE
    #------------------------------------------------------------------------
    
    def state_idle(self):

        log = logging.getLogger("agent.ping_manager.idle")

        log.info("Waiting for last cycle ending.")
    
        self.shared.receiver.receive.finalize(self.delta_M)
        self.shared.finishCycle=True
        log.info("Stop cycling and exit.")
             

      
    #------------------------------------------------------------------------
    # INTERNAL FUNCTIONS
    #------------------------------------------------------------------------
    """
    def api_call(self, fun, *args):
        for cpt in range(NB_RETRY + 1):
            ret = None
            try:
                ret = fun(*args)
                break
            except Exception, e:
                log = logging.getLogger("agent.ping_manager.api_call")
                log.info("Retrying %s: %s"  % (fun, e))
                pass
            time.sleep(1)
        if cpt > NB_RETRY:
            log = logging.getLogger("agent.ping_manager.api_call")
            log.error("Too many failures, aborting API calls")
            sys.exit(1)
        return ret
    """
    #----------------------------------------------------------------------
    
    def parse_config(self):
        self.manager=self.shared.parameters.MANAGER_DEFAULTS     
        self.delta_M    = timedelta(seconds = int(self.manager.get("delta_M")))
        self.ping_freq  = float(self.manager.get("ping_freq"))
        self.MAX_CYCLE  = int(self.manager.get("MAX_CYCLE"))

    #----------------------------------------------------------------------
