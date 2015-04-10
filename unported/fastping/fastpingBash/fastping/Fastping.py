from ThreadSender import ThreadSender
from ThreadReceiver import ThreadReceiver
from ThreadUploader import ThreadUploader
from SharedParameter import SharedParameter
from PARAMETERS import Parameters
import threading
import time
import logging


class Fastping():
    
    def __init__(self,deltaM,ping_freq,MAX_CYCLE,target,lowerUpper,filepath,saveRaw,saveCycleSummary,saveStat,saveQD,upload,queuingDelay):
        self.shared=SharedParameter(Parameters(deltaM,ping_freq,MAX_CYCLE,target,lowerUpper,filepath,saveRaw,saveCycleSummary,saveStat,saveQD,upload,queuingDelay))
        logging.basicConfig(filename=self.shared.parameters.log,level=logging.DEBUG, format='%(asctime)s %(name)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
       
            
    def run(self):
        threads = []
        self.event=threading.Event()
        # Create new threads
        sender = ThreadSender(1, "Thread Sender", self.event,self.shared)
        receiver= ThreadReceiver(2, "Thread Receiver", self.event, self.shared)
        uploader= ThreadUploader(3, "Thread Uploader", self.event, self.shared)
        
        self.shared.sender=sender
        self.shared.receiver=receiver
        self.shared.uploader=uploader
        
        # Start new Threads
        sender.start()
        receiver.start()
        uploader.start()
        # Add threads to thread list
        threads.append(sender)
        threads.append(receiver)
        threads.append(uploader)
       
        try:
        # Wait for all threads to complete
            while threading.active_count() > 1:  #while there is other thread active         
                for t in threads:
                    t.join(1)
        except KeyboardInterrupt:
                print "killing..." 
                self.event.set() #send message to all threads
                self.shared.uploaderCondition.acquire()                                
                self.shared.uploaderCondition.notifyAll() #wake up thread blocked on wait               
                self.shared.uploaderCondition.release()                
                a=time.time()
                for t in threads:
                    t.join()                
                print time.time()-a
#------------------------------Parameters------------------------------
    def setParameters(self,deltaM,ping_freq,MAX_CYCLE,target,lowerUpper,filepath,saveRaw,saveCycleSummary,saveStat,saveQD,upload,queuingDelay):
        self.shared.parameters=Parameters(deltaM,ping_freq,MAX_CYCLE,target,lowerUpper,filepath,saveRaw,saveCycleSummary,saveStat,saveQD,upload,queuingDelay)        
        
    #MANAGER SETTINGS
    def setDeltaM(self,deltaM):
         self.shared.parameters.MANAGER_DEFAULTS["delta_M"]=deltaM
    def setPingFreq(self,ping_freq):
         self.shared.parameters.MANAGER_DEFAULTS["ping_freq"]=ping_freq
    def setMaxCycle(self,MAX_CYCLE):
         self.shared.parameters.MANAGER_DEFAULTS["MAX_CYCLE"]=MAX_CYCLE
    #WORKING CYCLE SETTINGS
    def setDestinationFile(self,iplist_file):
         self.shared.parameters.CYCLE_DEFAULTS["iplist_file"]=iplist_file   
    def setLowerLimit(self,LOWER_LIMIT):
         self.shared.parameters.CYCLE_DEFAULTS["LOWER_LIMIT"]=LOWER_LIMIT   
    def setUpperLimit(self,UPPER_LIMIT):
         self.shared.parameters.CYCLE_DEFAULTS["UPPER_LIMIT"]=UPPER_LIMIT   
    #FOLDER
    def setFilePath(self,filepath):    
        self.shared.dir=filepath
     #QUEUING DELAY
    def setQdLower(self,qd_lower):
        self.shared.qd_lower=qd_lower
    def setQdUpper(self,qd_upper):
        self.shared.qd_upper=qd_upper
    def setQdInterval(self,qd_interval):
        self.shared.qd_interval=qd_interval
    #OUTPUTFILE
    def setSaveRawStat(self,RW):
        self.shared.RW=RW
    def setSaveCycleSummary(self,SM):
        self.shared.SM=SM
    def setSaveStat(self,ST):
        self.shared.ST=ST
    def setSaveQueuingDelay(self,QD):
        self.shared.QD=QD
#----------------------------------------------------------------------

