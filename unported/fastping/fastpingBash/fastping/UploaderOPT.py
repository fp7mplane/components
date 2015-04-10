#/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# IMPORTS + LOGGING + CONST DEFINITION
#------------------------------------------------------------------------

from __future__     import with_statement
from os.path        import join
from threading      import Condition

from Stats             import Stats
from UploadOPT         import UploadOPT


import os, time, random, shutil, logging


#STATS_DIR = shared.parameters.STATS_DIR
#STATS_BACKUP_DIR = PARAMETERS().RAW_DIR
STATS_BACKUP_DIR = None

def check_directory(path):

    log = logging.getLogger('agent.logger')
    
    # Check directory existence and type
    if os.access(path, os.F_OK):
        if not os.path.isdir(path):
            log.critical("Path '%s' exists and is not a directory" % path)
    
    # Create directory if necessary
    else:
        try:
            os.makedirs(path)
            log = logging.getLogger("agent")
            log.info("Directory '%s' did not exist, created it." % path)
        except:
            log.critical("Directory '%s' does not exist and cannot be created" % path)
    
    # Check writability
    if not os.access(path, os.W_OK):
        log.critical("Directory '%s' is not writable" % path)

#------------------------------------------------------------------------
# PARSING UPLOADER CLASS
#------------------------------------------------------------------------       

class UploaderOPT():
    def initialize(self,shared,condition):
        self.shared=shared       
        self.memory = []                # buffer of files to upload
        self.last_error = None          # last error 
        self.ts = 0                     # timestamp used to set retry waiting
        self.backoff = 0                # value used to calculate retry interval
        self.STATS_DIR=shared.parameters.STATS_DIR
        self.RAW_DIR=shared.parameters.RAW_DIR        
        self.condition = condition    # conditional variable for memory access
 
        self.baselines = {}             # min{RTT} for each target
        self.is_bufferbloat = {}        # identify if there's bufferbloat for each target
        
    #------------------------------------------------------------------------

    def save_static(self,_stats_ref,_id):
        
        ts = int(_stats_ref.startTime)
        cycle = int(_stats_ref.cycle)
        
        if self.shared.parameters.SAVE_RW:
            raw_filename = "%s_%s.rw" % (_id,ts)
           # raw_file = open(os.path.join(self.RAW_DIR, raw_filename),'r')
            self.uploader_file(os.path.join(self.RAW_DIR, raw_filename))            
            #raw_file.close()
            
        if self.shared.parameters.SAVE_ST:
            out_filename = "%s_%s-%d.st" % (_id,ts,cycle)
            out_file = open(os.path.join(self.STATS_DIR,out_filename),'w')
            out_file.write("#target_ID\ttargetIP\tsentPackets\treceivedPackets\tlastTTL\taverageRTT\taverageQD\tsampleVarianceQD\tbaseline(minQD)\tmaxQD\tpercentile10\tpercentile25\tperncentile50\tpercentile75\tpercentile90\tstate\n")        
            out_file.write(_stats_ref.stats_toString())
            self.uploader_file(out_file.name)
            out_file.close()      
		
        if self.shared.parameters.SAVE_SM:
            summ_filename = "%s_%s-%d.sm" % (_id,ts,cycle)
            summ_file = open(os.path.join(self.STATS_DIR,summ_filename),'w')
            summ_file.write("#ID\tPREC\tTYPE\tVAL\t%\n")        
            summ_file.write(_stats_ref.get_summary())
            self.uploader_file(summ_file.name)            
            summ_file.close()
            

        if self.shared.parameters.SAVE_QD:
            qd_filename = "%s_%s-%d.qd" % (_id,ts,cycle)
            qd_file = open(os.path.join(self.STATS_DIR,qd_filename),'w')
            qd_file.write("#X\tPDF\tCDF\tiCDF\n")
            qd_file.write(_stats_ref.get_qd())
      	    self.uploader_file(qd_file.name)
            qd_file.close()          
    
    #------------------------------------------------------------------------
    
    def uploader_file(self, f):
        
        self.condition.acquire()        # ask for exclusive memory access
        self.memory.append(f)           # ask for scheduling
        self.condition.notify()         # notify memory availability
        self.condition.release()        # release memory
       
    #------------------------------------------------------------------------

    def state_process(self):

        log = logging.getLogger('agent.uploader.process')
        
        # VERIFY UPLOAD REQUESTS
        self.condition.acquire()                        # exclusive memory access 
        while not self.shared.finishCycle:
     
            ts = time.time()                            # get actual time
            if self.memory:                             # IF uploads are waiting -> ...               [1/4]
                if self.ts <= ts:                       # ... -> IF RETRY WAIT is settled ->-> ...    [2/4]
                    self.ts = ts            
                    break
               
                self.condition.wait(self.ts - ts)       # ... ->-> wait before retrying               [3/4]
            else:                                                      
                self.condition.wait()                   # ... -> ELSE empty memory wait               [4/4]
                if(self.shared.uploader.event.is_set()):
                    return
        self.condition.release()                        # release memory
       
        # FILE UPLOADING
        err = UploadOPT().call(self.memory,self.shared)     

        # GET A STATUS FOR ALL FILES
        reattempt = []                  # file to which retry upload
        success = 0                     # number of uploaded files 
        for f in self.memory:
            if f in err:                                        # IF f has not been loaded -> ...         [1/2]
                log.error("File %s: ERROR %s" % (f, err[f]))
                self.last_error = err[f]                        
                reattempt.append(f)                             # ... -> retry uploading for that file    [2/2]
            else:
                success += 1                                    # increment succeeded_file count
              
                # Move uploaded file somewhere else  
                if STATS_BACKUP_DIR is not None:
                    f_name = os.path.basename(f)
                    shutil.move(join(self.STATS_DIR,f_name),join(STATS_BACKUP_DIR,f_name))
                else:
                    os.unlink(f)

        self.memory = []

        # CALCULATE RETRY WAITING
        if success > 0:
            self.backoff = 0            # reset limit
        else:
            if self.backoff < 10:
                self.backoff += 1       # increment limit

        if reattempt:
            delay = random.randint(1, 2 ** self.backoff)        # calculate random retry waiting
            self.ts += delay
            
            # REINSERT FILES INTO MEMORY
            self.condition.acquire()
            self.memory.extend(reattempt)
            self.condition.notify()
            self.condition.release()
        
        return 'process'


 #------------------GLUE CODE-----------------------------
    def save_stats(self,_stats_ref,_id):
        log = logging.getLogger('agent.uploader.save')
        

        try: 
            self.save_static(_stats_ref,_id)
            log.info("Uploading stats...")
        except Exception, e:
            log.error("%s" % e)
 #-----------------------------------------------
    def upload_file(self,path, filename):
        try: 
            self.uploader_file(os.path.join(path, filename))# insert path/filename into ParsingUploader()::memory
        except Exception, e:
            log = logging.getLogger('agent.uploader.upload')
            log.error("%s casdasda" % e)
#----------------------------------------------------------------------------

