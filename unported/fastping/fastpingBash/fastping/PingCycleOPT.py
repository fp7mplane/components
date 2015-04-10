#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Performs a round of ping towards all destinations """

#------------------------------------------------------------------------
# IMPORTS + LOGGING + CONST DEFINITION
#------------------------------------------------------------------------

import time, logging, sys, struct, socket, random

from DestList       import DestList
from Stats          import Stats



#------------------------------------------------------------------------
# PING CYCLE (OPT) CLASS
#------------------------------------------------------------------------

class PingCycleOPT:
                      
    #------------------------------------------------------------------------
    # ++ METHOD 01: INITIALIZATION
    #------------------------------------------------------------------------

    def __init__(self,shared, deltaM, freq,_skt):
        self.countCycle = 0                     # cycle ID NUMBER
        self.dM = deltaM                        # ping measurement interval
        self.f = freq                           # ping frequency
      
        self.dests = None                       # list of ping destinations
        self.nDests = 0                         # number of destinations
        
        self.socket = _skt                      # socket reference
        self.seq = 0                            # sequence number
        self.end_time = 0                       # end of the current slot
        self.stop_cycle = 0                     # end of the current cycle
        
        self.penalty = 0                        # delay counter
        self.ANS_LIMIT = 10                     # answer timeout [s]
        self.shared=shared
 

        # LOAD PARAMETERS
        self.parse_config()          # load configuration 
        self.preload_destinations()             # load destinations list  
        shared.destList=self.dests   #update destination
            
            
    #------------------------------------------------------------------------
    # ++ METHOD 02: PRELOAD DESTINATIONS
    #------------------------------------------------------------------------

    def preload_destinations(self,_increment=False):
        try:
            log = logging.getLogger("agent.ping_cycle.preload")
            self.dests = DestList()
            #file_dest = open(self.iplist_file,'r')
            with open(self.shared.parameters.filePath +'/iplist.dat') as f:
                self.destination=[line.rstrip() for line in f]            
            try:
                for dest_ip in self.destination:
                    #if dest_id == self.hostname:
                        self.shared.check_killed("Sender",self.shared.sender.event)# check Sendere received killing signal.
                        if self.UPPER_LIMIT != -1 and self.nDests > self.UPPER_LIMIT-1:
                                break
                        index = dest_ip.find("/")
                        try:
                            if index != -1:                                                                                                                     # is it a subnet?
                                socket.inet_aton(dest_ip[:index])                                                                                               # check ip_validity
                                net = self.networkMask(dest_ip[:index],int(dest_ip[(index+1):]))                                                                # get subnet address
                                addr = net+1                                                                                                                    # JUMP subnet address
                                while self.addressInNetwork(addr,net,int(dest_ip[(index+1):])) and (self.UPPER_LIMIT == -1 or (self.UPPER_LIMIT != -1 and self.nDests < self.UPPER_LIMIT-1)):    # is IP into subnet?
                                    if self.nDests >= self.LOWER_LIMIT-1:
                                        self.dests.insert(self.numToDottedQuad(addr))              
                                    self.nDests += 1
                                    addr += 1
                                
                                if self.addressInNetwork(addr,net,int(dest_ip[(index+1):]))==False:
                                    if self.nDests >= self.LOWER_LIMIT-1:
                                        self.dests.remove_last()                                            # JUMP broadcast address
                                    self.nDests -= 1                                                        # correct self.nDests
                                    
                            else:
                                if self.nDests >= self.LOWER_LIMIT-1:
                                    addr = socket.gethostbyname(dest_ip)                                       # CHECK VALIDITY and (if necessary) convert NAME into IP
                                    self.dests.insert(addr)  #-------------------> problem: takes a lot of time socket.gethostbyname(dest_ip)
                                   
                                self.nDests += 1
                                
                        except socket.error:
                            if index != -1:
                                log.error("Invalid IP: %s" % dest_ip[:index])
                            else:
                                log.error("Invalid IP: %s" % dest_ip)
                      #-------------------------------------------------for testing
                        #b=time.time()-a   # a time.time before try
                        #if time.time()-a>1:
                         #   print dest_ip 
                          #  print b
                    #-------------------------------------------------for testing
                self.nDests = self.nDests - max(self.LOWER_LIMIT,1) + 1
                log.info("Loaded targets: %d" % self.nDests)
            
            except why: #eliminare tutto i csv
                log.error("TracerouteCycle::preload_destinations(): file %s, %s" % (self.iplist_file, why))
        
        except Exception, why:
            log.error("Exception preload destination:")
            log.error(why)
    
    #------------------------------------------------------------------------
            
    def makeMask(self,n):
        "return a mask of n bits as a long integer"
        return long('1'*n+'0'*(32-n),2)

    def dottedQuadToNum(self,ip):
        "convert decimal dotted quad string to long integer"
        return struct.unpack('>L',socket.inet_aton(ip))[0]

    def networkMask(self,ip,bits):
        "Convert a network address to a long integer" 
        return self.dottedQuadToNum(ip) & self.makeMask(bits)

    def addressInNetwork(self,ip,net,bits):
        "Is an address in a network"
        return (ip & self.makeMask(bits)) == (net & self.makeMask(bits))
    
    def numToDottedQuad(self,n): 
        "convert long int to dotted quad string" 
        return socket.inet_ntoa(struct.pack('>L',n))
            
            
        
    #------------------------------------------------------------------------
    # ++ METHOD 03: FIRST PING + REINITIALIZATION
    #------------------------------------------------------------------------

    def run(self):
        try:
            
            log = logging.getLogger("agent.ping_cycle.run")
            
            self.seq = 0                                                        # reset sequence number
            self.penalty = 0
            self.avg_time = 0.0
                
            now = time.time()                                                   # current time
            
            #self.end_time = now - (now % self.dM.seconds) + self.dM.seconds     # end time of current measurement CYCLE
            self.end_time = now + self.dM.seconds                               # end time of current measurement CYCLE
            
            #self.stop_cycle = now - (now % self.f)                              # end time of current measurement
            self.stop_cycle = now
        
            while now < self.end_time:
                self.stop_cycle += self.f
                
                count = 0
                start = time.time()
                for id in range(self.dests.size):
                    if self.shared.stats.state_list[id] == 0:                                                              # ACTIVE_IP check
                        now = time.time()
                        if self.shared.stats.packets[id][2] > now-self.ANS_LIMIT:                                        # UNRECEIVED_ANSWER check -> if penalty, extends interval
                            if self.dests.full_list[id] != "":                                       # VALID_IP check
                                count+=1
                                self.send_one_ping(self.dests.full_list[id],id,self.seq)             # --> PING EXECUTION
                                self.shared.stats.update_sent(id)
                            else:
                                log.error("Invalid IP address %s" % self.dests.full_list[id])
                        else:
                            self.shared.stats.state_list[id] = -1   
                
                #print count
                now = time.time()
                self.avg_time = (self.avg_time*self.seq + (now-start))/(self.seq+1)
                
                # LIMIT PINGING TO AT MOST 1 ping/s
                if now < self.stop_cycle:                    # if there's still time -> ...
                    wait_time = self.stop_cycle-now
                    if(self.shared.sender.event.wait(wait_time)): #...->wait for next cycle:Reentrant lock: if there is a set, it will unlock and it will return true                        
                        return
                    
                self.seq += 1                                   # increment sequence number
            
            self.shared.stats.avg_time = self.avg_time
            log.info("End of cycle %d - avg_time: %f" % (self.countCycle,self.avg_time))
           
        except Exception, e:
            log.error("%s" % e)
            log.warning("ENOBUFS in cycle %d. Jump 1 cycle." % self.countCycle)
            now = time.time()
            if(self.shared.sender.event.wait(self.dM.seconds-(now-self.shared.stats.startTime))): #Reentrant lock: if there is a set, it will unlock and it will return true                        
                return
       
    
    #------------------------------------------------------------------------
    # ++ METHOD 04: SUPPORT METHODS
    #------------------------------------------------------------------------
            
    def send_one_ping(self,target,my_ID,seq):
        #self.message="ow.ly/wPjH6"
        # HEADER -> type (8bit), code (8bit), checksum (16bit), id (16bit), sequence (16bit)
        my_checksum = 0
        rdm_ID = random.randint(1, 65535) & 65535
        # Make dummy header with 0 checksum.
        header = struct.pack('bbHHh', self.ICMP_ECHO_REQUEST, 0, my_checksum, rdm_ID, seq)
        bytesInDouble = struct.calcsize('d')                                                    # SEND_TIME field size 
        bytesInInt = struct.calcsize('i')                                                       # ID field size
        #data = (self.PACKET_SIZE - len(header) - 2*bytesInInt - bytesInDouble) * 'x'            # fill remaining pkt with 'x'
        data = (self.shared.parameters.packet_size - len(header) - 2*bytesInInt - bytesInDouble) * 'x'
        start = time.time()
       
        data = struct.pack('i',my_ID) + struct.pack('i', self.countCycle) + struct.pack('d', start)+data 
        #data = struct.pack('i',my_ID) + struct.pack('i', self.countCycle) + struct.pack('d', start) + self.message
        # CALCULATE data checksum and dummy header.
        my_checksum = self.checksum(header + data)

        # CREATE NEW HEADER [with corrected checksum]
        header = struct.pack('bbHHh', self.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), rdm_ID, seq)
        packet = header + data
        
        # SEND PACKET
        while packet:
            sent = self.socket.sendto(packet,(target, 1))
            packet = packet[sent:]  
                 
            
    #----------------------------------------------------------------------------------------#
    def checksum(self,source_string):
        
        s = 0
        countTo = len(source_string) / 2 * 2
        count = 0
        while count < countTo:
            thisVal = ord(source_string[count + 1]) * 256 + ord(source_string[count])
            s = s + thisVal
            s = s & 0xffffffff  # Necessary?
            count = count + 2
    
        if countTo < len(source_string):
            s = s + ord(source_string[len(source_string) - 1])
            s = s & 0xffffffff  # Necessary?
    
        s = (s >> 16) + (s & 65535)
        s = s + (s >> 16)
        answer = ~s
        answer = answer & 65535
        
        answer = answer >> 8 | answer << 8 & 0xff00
    
        return answer

    #------------------------------------------------------------------------
  
    def parse_config(self):
        """
        \brief     Parse configuration file and initialize: self.iplist_file
        \param filename     Configuration_file path
        """
        self.cycleDefaults=self.shared.parameters.CYCLE_DEFAULTS     
        self.iplist_file=self.cycleDefaults.get("iplist_file")   
        self.LOWER_LIMIT = self.cycleDefaults.get("LOWER_LIMIT")
        self.UPPER_LIMIT = self.cycleDefaults.get("UPPER_LIMIT")
        self.ICMP_ECHO_REQUEST =8
        self.PACKET_SIZE = 32 #PACKETSIZE
        
    #------------------------------------------------------------------------
