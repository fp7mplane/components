#/usr/bin/env python
# -*- coding: utf-8 -*-
""" Manage parsing and uploading of output files """

#------------------------------------------------------------------------
# IMPORTS + LOGGING + CONST DEFINITION
#------------------------------------------------------------------------

from threading          import Condition
from Stats         import Stats
from DestList      import DestList

import os, time
import logging, select, sys, struct, socket

   
#------------------------------------------------------------------------

def check_directory(path):

    log = logging.getLogger('agent.ping_listener.check_dir')
    
    # Check directory existence and type
    if os.access(path, os.F_OK):
        if not os.path.isdir(path):
            log.critical("Path '%s' exists and is not a directory" % path)
    
    # Create directory if necessary
    else:
        try:
            os.makedirs(path)
            log.info("Directory '%s' did not exist, created it." % path)
        except:
            log.critical("Directory '%s' does not exist and cannot be created" % path)
    
    # Check writability
    if not os.access(path, os.W_OK):
        log.critical("Directory '%s' is not writable" % path)

#------------------------------------------------------------------------
# PARSING UPLOADER CLASS
#------------------------------------------------------------------------       

class PingListener():
    """ Manage parsing and uploading of output files """

    def __init__(self, Shared):
        self.shared=Shared 
        
#------------------------------------------------------------------------
# State 01: Initialize
#------------------------------------------------------------------------

    def initialize(self):
        
        self.agent_hostname=self.shared.hostname #Danilo
        # Initialize FSM
        self.memory = []                # buffer of files to upload        
        self.old_stats = None
        self.new_stats = None
        
        self.old_raw_file = None
        self.new_raw_file = None
        
        self.dests = self.shared.destList             
        self.countCycle = 0
        self.condition = Condition()
        
        self.start = time.time()
        self.old = 0
        self.out = 0
        self.count=0#delete
 #------------------------------------------------------------------------
 # State 01: Initialize
 #------------------------------------------------------------------------
           
    def state_sync(self):
        
        while self.shared.socket == None or self.old_stats == None: #wait a command: 1 cycle:open socket or old stats 
            if(self.shared.receiver.event.wait(0.1)): #Reentrant lock: if there is a set, it will unlock and it will return true                        
                return
            

        log = logging.getLogger('agent.ping_listener.initialize')
        log.info("State 01 finished")
        
        return 'listen'

 #------------------------------------------------------------------------
 # State 02: State Listen
 #------------------------------------------------------------------------
    def state_listen(self):     
        
        try:
                    log = logging.getLogger('agent.ping_listener.listen')
            
            #whatReady = select.select([self.shared.socket], [], [],3) # 3 seconds timeout understand more!                   
            #if whatReady[0] != []:
                #for skt in whatReady[0]:     
                   
                    skt= self.shared.socket 
                    # get datas
                    (recPacket, addr) = skt.recvfrom(self.shared.parameters.packet_size)
                    timeReceived = time.time()
                    icmpHeader = recPacket[20:28]
                    (type, code, checksum, packetID, sequence) = struct.unpack('bbHHh', icmpHeader)
                    bytesInInt = struct.calcsize('i')
                    bytesInDouble = struct.calcsize('d')
                   
                    # VALID ANSWER                
                    if type == 0:
                        dest = None                    
                        try:
                            targetID = struct.unpack('i', recPacket[28:28 + bytesInInt])[0]
                            dest = self.shared.destList.get_target(targetID)
                        except:
                            pass
                        if dest == addr[0] and self.old_stats != None:
                           
                            nCycle = struct.unpack('i', recPacket[28 + bytesInInt:28 + 2*bytesInInt])[0]
                            timeSent = struct.unpack('d', recPacket[28 + 2*bytesInInt:28 + 2*bytesInInt + bytesInDouble])[0]
                            self.timeSent=struct.unpack('d', recPacket[28 + 2*bytesInInt:28 + 2*bytesInInt + bytesInDouble])[0]
                            aRTT = timeReceived-timeSent 
                            ttl = struct.unpack('b',recPacket[8:9])[0]
                            if(aRTT<0):                            
                                print aRTT

                            # OLD CYCLE PACKET
                            if self.countCycle == 1 or (nCycle == self.countCycle-1):
                                self.old_stats.update_rcvd(targetID,aRTT,ttl,timeReceived)
                               
                                if self.countCycle != 1:
                                    self.old += 1
                                self.condition.acquire()                                
                                if self.old_raw_file != None:
                                    self.old_raw_file.write(str(targetID)+"\t"+str(addr[0])+"\t"+str(sequence)+"\t"+str(nCycle)+"\t"+'{0:.4e}\t {1:.11f}\t {2:.11f}\n'.format(aRTT,timeReceived,timeSent))
                               
                                self.condition.notify()        
                                self.condition.release()   
                            
                            # NEW CYCLE PACKET
                            elif nCycle == self.countCycle:
                                self.new_stats.update_rcvd(targetID,aRTT,ttl,timeReceived)
                                self.condition.acquire()
                                if self.new_raw_file != None:
                                    self.new_raw_file.write(str(targetID)+"\t"+str(addr[0])+"\t"+str(sequence)+"\t"+str(nCycle)+"\t"+'{0:.4e}\t {1:.11f}\t {2:.11f}\n'.format(aRTT,timeReceived,timeSent))
                                self.condition.notify()        
                                self.condition.release()
                            else:
                                self.out += 1
                        
                    # INVALID ANSWER    
                    elif type == 3:
                        targetID = -1
                        try:
                            targetID = struct.unpack('i', recPacket[56:56 + bytesInInt])[0]
                        except struct.error:
                            (addr1,addr2,addr3,addr4) = struct.unpack('BBBB', recPacket[44:48])
                            a = "%d.%d.%d.%d"%(addr1,addr2,addr3,addr4)
                            try:
                                targetID = self.dests.full_list.index(str(a))
                            except:
                                try:
                                    targetID = self.dests.full_list.index(str(addr[0]))
                                except:
                                    pass
                        
                        if self.countCycle > 1:
                            self.new_stats.state_list[targetID] = code
                        else:
                            self.old_stats.state_list[targetID] = code

                    else:
                        #>>>>>>> CORREGGI IL TIPO 11
                        #log = logging.getLogger('agent.ping_listener.listen')
                        #log.warning("Invalid type -> IP: %s - type: %d" % (addr[0],type))
                        pass
                    
                    log.info("State02: received correct")
        except Exception,e:
            
            #log.error("%s" % e)
            log.error("%s" % e)       
        log.info("State 02 finished")
        return 'listen'
 
#update old_stats and new_stats
    def set_stats(self,_stats_ref,_file_ref=None,_is_last=False):
        self.countCycle += 1     
        self.condition.acquire()
        if self.old_stats != None:                          # identify SECOND/MIDDLE cycle
            
            if self.new_stats != None or _is_last:          # identify MIDDLE cycle
                log = logging.getLogger('agent.ping_listener.set_stats')
                log.info("Cycle %d receiving timeout - n_old_pkts: %d - n_out_pkts: %d" % (self.countCycle-2,self.old,self.out))
                self.old = 0
                self.out = 0
                
                if self.old_raw_file != None:
                    self.old_raw_file.close()
                self.shared.uploader.upload.save_stats(self.old_stats,self.shared.hostname)                    
               
                self.old_stats = self.new_stats
                self.new_stats = _stats_ref
                                                   
                self.old_raw_file = self.new_raw_file
                self.new_raw_file = _file_ref

            else:                                           # identify SECOND cycle
                self.new_stats = _stats_ref
                self.new_raw_file = _file_ref
        
        else:
                                                          # identify FIRST cycle
            self.old_stats = _stats_ref
            self.old_raw_file = _file_ref
        
        self.condition.notify()        
        self.condition.release()
        
    
    def finalize(self,_delta):
        log = logging.getLogger('agent.ping_listener.finalize')
        log.info("-------------------------")
        self.set_stats(None,None)
        if(self.shared.sender.event.wait(_delta.seconds)): #Reentrant lock: if there is a set, it will unlock and it will return true                        
            return
        #time.sleep(_delta.seconds) 
        self.set_stats(None,None,True)
        """
        try:
            if self.shared.socket is not None: #control if it is close and find the code                
                self.shared.socket.shutdown(socket.SHUT_RDWR)                                
        except Exception, e:
            print "sdasda"
            print e
        """        
        try:  
            self.shared.socket.shutdown(socket.SHUT_RDWR) # SHUT_RD=0 , SHUT_WR=1 , SHUT_RDWR=2
        #except OSError as exc : #I have to upload to python 3.3 and after change next lines 
        except socket.error as exc: #---> skip error
        #print ('shutdown  os error  %s' % str (exc))
            exc            
        self.shared.socket.close()                                
        
