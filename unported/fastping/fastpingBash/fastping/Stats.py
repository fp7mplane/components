
import time, logging
from DestList          import DestList
from PercMarkers       import PercMarkers


class Stats():
    
    def __init__(self,_list_ref,_size,_start,_cycle,parameter):     
        
        self.dest_list = _list_ref
        self.size = _size
        self.startTime = _start
        self.cycle = _cycle
        self.avg_time = 0.0
        
        self.packets = []                           # [N_sent_pkt, N_rcvd_pkt, last_rcvd_time]
        self.average = []                           # [qd average]
        self.average_RTT = []                       # [RTT average]
        self.variance = []                          # [RTT variance]
        self.baseline = []                          # [MIN RTT]
        self.qd_max = []                            # [MAX QD]
        self.qd_percs = []                          # [perc10, perc25, perc50, perc75. perc90]
        self.ttl = []
        
        self.state_list = []
        
        self.qd_upper = float(parameter.qd_upper)
        self.qd_lower = float(parameter.qd_lower)
        self.qd_interval = float(parameter.qd_interval)
        
        self.up_pfx = "qd_%%.%df+" % parameter.qd_cyphers
        self.lw_pfx = "qd_%%.%df-" % parameter.qd_cyphers
        self.md_pfx = "qd_%%.%df-%%.%df" % (parameter.qd_cyphers,parameter.qd_cyphers)
        
        # SUMMARY SETTING
        self.summary = {"tot_sent":0, "tot_rcvd":0, "all_rcvd":0, "one_rcvd":0, "no_ans":0, "rep":0, "inh":0, 
                        "loss_0-25":0, "loss_25-50":0, "loss_50-75":0, "loss_75-100":0, 
                        "rtt_0.00-0.25":0, "rtt_0.25-0.50":0, "rtt_0.50-0.75":0, "rtt_0.75-1.00":0, "rtt_1.00-2.00":0, "rtt_2.00+":0}
        
        # QUEUING DELAY INTERVALS SETTING
        # first interval
        key = self.lw_pfx % (self.qd_lower)
        self.summary[key] = 0 
        
        # middle intervals
        limit = self.qd_lower
        while limit < self.qd_upper:
            key = self.md_pfx % (limit,limit+self.qd_interval)
            self.summary[key] = 0 
            limit += self.qd_interval
        
        # last interval
        key = self.up_pfx % (self.qd_upper)
        self.summary[key] = 0 
        
        # STATS LIST INITIALIZATION
        for i in range(_size):
            self.insert()
            
    #------------------------------------------------------------------------
        
    def insert(self,_sent=0,_rcvd=0,_avg=0.0,_avgRTT=0.0,_var=0.0,_min=0.0,_max=0.0,_ttl=0,_p=[0.1,0.25,0.5,0.75,0.9],_state=0):
        now = time.time()
        self.packets.append([_sent,_rcvd,now])
        self.average.append(_avg)
        self.average_RTT.append(_avgRTT)
        self.variance.append(_var)
        self.baseline.append(_min)
        self.qd_max.append(_max)
        self.qd_percs.append(PercMarkers(_p))
        self.ttl.append(_ttl)
        
        self.state_list.append(_state)
       
        
        
    #------------------------------------------------------------------------
        
    def update_sent(self,_id):
        self.packets[_id][0]+=1
        self.summary["tot_sent"]+=1
       
    #------------------------------------------------------------------------
    
    def update_rcvd(self,_id,_aRTT,_ttl,_time):
        self.packets[_id][1]+=1
        self.packets[_id][2]=_time
        self.state_list[_id]=0
            
        self.ttl[_id]=_ttl
        self.summary["tot_rcvd"]+=1
        
        if self.baseline[_id]==0.0:
            self.baseline[_id]=_aRTT
        else:
            self.baseline[_id]=min(self.baseline[_id],_aRTT)
        
        self.average_RTT[_id]=(self.average_RTT[_id]*(self.packets[_id][1]-1)+_aRTT)/self.packets[_id][1]
        
        try:
            
            q_del = _aRTT - self.baseline[_id]
            
            delta = q_del-self.average[_id]
            self.average[_id]=(self.average[_id]*(self.packets[_id][1]-1)+q_del)/self.packets[_id][1]
            self.variance[_id]=self.variance[_id]+delta*(q_del-self.average[_id])                          # remember to divide for (self.packets[_id][1]-1) at the end
        
            self.qd_max[_id]=max(self.qd_max[_id],q_del)
            
            if q_del >= self.qd_upper:
                key = self.up_pfx % (self.qd_upper)
                self.summary[key] += 1
            elif self.qd_lower < q_del and q_del < self.qd_upper:
                limit = float(int(q_del/self.qd_interval))*self.qd_interval
                key = self.md_pfx % (limit,limit+self.qd_interval)
                self.summary[key] += 1
            else:
                key = self.lw_pfx % (self.qd_lower)
                self.summary[key] += 1
                
            self.qd_percs[_id].add_value(q_del)
                
        except Exception, e:
            log = logging.getLogger('agent.stats.up_rcvd')
            log.error("%s" % e)
        #print("Update_rcvd %s %s %s %s",_id,_aRTT,_ttl,_time)
    #------------------------------------------------------------------------
    
    """  
    def set_inhibited(self,_id,_code):
            target = self.dest_list.full_list[_id]
            self.inhibited[target] = [_id,_code]
    """
         
    #------------------------------------------------------------------------
        
    def get_sent(self,_id):
        return self.packets[_id][0]
    
    def get_rcvd(self,_id):
        return self.packets[_id][1]       
    
    def get_last(self,_id):
        return self.packets[_id][2]
    
    def get_avg(self,_id):
        return self.average[_id]
    
    def get_var(self,_id):
        return self.variance[_id]
    
    def get_max(self,_id):
        return self.qd_max[_id]
        
    def get_perc(self,_id,_p=None):
        return self.qd_percs[_id].get_perc(_p)
    
    #------------------------------------------------------------------------
    def stats_toString(self,_id=None):
       
        temp = ""
        try:
            if _id == None:
                for i in range(self.size):
                    self.set_stats_summary(i)                
                    temp += "%d\t%s\t%d\t%d\t%d\t%.8e\t" % (i, self.dest_list.get_target(i), self.packets[i][0], self.packets[i][1], self.ttl[i], self.average_RTT[i])          
                    temp += "%.8e\t%.8e\t%.8e\t%.8e\t" % (self.average[i], (self.variance[i]/max(self.packets[i][1]-1,1)), self.baseline[i], self.qd_max[i])
                    temp += "%s\t%d\n" % (self.qd_percs[i].toString(),self.state_list[i])
            else:
                temp += "%d\t%s\t%d\t%d\t%d\t%.8e\t" % (i, self.dest_list.get_target(_id), self.packets[_id][0], self.packets[_id][1], self.ttl[_id], self.average_RTT[_id])
                temp += "%.8e\t%.8e\t%.8e\t%.8e\t" % (self.average[_id], (self.variance[_id]/max(self.packets[_id][1]-1,1)), self.baseline[_id], self.qd_max[_id])    
                temp += "%s\t%d\n" % (self.qd_percs[_id].toString(),self.state_list[_id])
                
        except Exception, e:
            log = logging.getLogger('agent.stats.stats_toString')
            log.error("%s" % e)  
        return temp

 
    #------------------------------------------------------------------------
    
    def get_summary(self):        
        
        temp = ""
        try:
            
            N_rep = self.size - self.summary["no_ans"]
            N_rep = max(N_rep,1)
            
            # STRUCTURE: name    class    value    perc
            temp  = "AVG_TIME\tROOT\tPERF\t%.4f\n" % (self.avg_time)
            
            temp += "RCVD_PKTS\tROOT\tPKT\t%d\t%.2f\n" % (self.summary["tot_rcvd"], (float(self.summary["tot_rcvd"])/float(self.summary["tot_sent"]))*100)
            temp += "SENT_PKTS\tROOT\tPKT\t%d\n" % (self.summary["tot_sent"])
            
            temp += "TOT_TARGETS\tROOT\tTARGET\t%d\n" % (self.size)
            temp += "REPLIED\tROOT\tTARGET\t%d\t%.2f\n" % (N_rep, (float(N_rep)/self.size)*100)
            temp += "ALL_RCVD\tREPLIED\tTARGET\t%d\t%.2f\n" % (self.summary["all_rcvd"], (float(self.summary["all_rcvd"])/self.size)*100)
            temp += "LOSS_0-25\tREPLIED\tTARGET\t%d\t%.2f\n" % (self.summary["loss_0-25"], (float(self.summary["loss_0-25"])/self.size)*100)
            temp += "LOSS_25-50\tREPLIED\tTARGET\t%d\t%.2f\n" % (self.summary["loss_25-50"], (float(self.summary["loss_25-50"])/self.size)*100)
            temp += "LOSS_50-75\tREPLIED\tTARGET\t%d\t%.2f\n" % (self.summary["loss_50-75"], (float(self.summary["loss_50-75"])/self.size)*100)
            temp += "LOSS_75-100\tREPLIED\tTARGET\t%d\t%.2f\n" % (self.summary["loss_75-100"], (float(self.summary["loss_75-100"])/self.size)*100)
            temp += "ONE_RCVD\tLOSS_75-100\tTARGET\t%d\t%.2f\n" % (self.summary["one_rcvd"], (float(self.summary["one_rcvd"])/self.size)*100)
            temp += "REPLICATED\tREPLIED\tTARGET\t%d\t%.2f\n" % (self.summary["rep"], (float(self.summary["rep"])/self.size)*100)
            temp += "UNREPLIED\tROOT\tTARGET\t%d\t%.2f\n" % (self.summary["no_ans"], (float(self.summary["no_ans"])/self.size)*100)
            temp += "INHIBITED\tUNREPLIED\tTARGET\t%d\t%.2f\n" % (self.summary["inh"], (float(self.summary["inh"])/self.size)*100)
            
            temp += "RTT_0.00_0.25\tROOT\tRTT\t%d\t%.2f\n" % (self.summary["rtt_0.00-0.25"], (float(self.summary["rtt_0.00-0.25"])/N_rep)*100) 
            temp += "RTT_0.25_0.50\tROOT\tRTT\t%d\t%.2f\n" % (self.summary["rtt_0.25-0.50"], (float(self.summary["rtt_0.25-0.50"])/N_rep)*100)
            temp += "RTT_0.50_0.75\tROOT\tRTT\t%d\t%.2f\n" % (self.summary["rtt_0.50-0.75"], (float(self.summary["rtt_0.50-0.75"])/N_rep)*100)
            temp += "RTT_0.75_1.00\tROOT\tRTT\t%d\t%.2f\n" % (self.summary["rtt_0.75-1.00"], (float(self.summary["rtt_0.75-1.00"])/N_rep)*100)
            temp += "RTT_1.00_2.00\tROOT\tRTT\t%d\t%.2f\n" % (self.summary["rtt_1.00-2.00"], (float(self.summary["rtt_1.00-2.00"])/N_rep)*100)
            temp += "RTT_2.00+\tROOT\tRTT\t%d\t%.2f\n" % (self.summary["rtt_2.00+"], (float(self.summary["rtt_2.00+"])/N_rep)*100)
            
        except Exception, e:
            log = logging.getLogger('agent.stats.summary')
            log.error("%s" % e)
            
        return temp

    #------------------------------------------------------------------------
    
    def get_qd(self):
        
        qd_string = ""
        try:
            cdf = 0.0                                   # cdf buffer
            qd_num = max(self.summary["tot_rcvd"],1)    # normalization factor
            
            # first interval
            limit = self.qd_lower
            key = self.lw_pfx % (self.qd_lower)         # key
            temp = float(self.summary[key])             # PDF
            cdf += temp                                 # CDF
            qd_string += "%.8f\t%.8f\t%.8f\t%.8f\n" % (limit-self.qd_interval/2,temp/qd_num,cdf/qd_num,1-cdf/qd_num) 
            
            # middle intervals                       
            while limit < self.qd_upper:
                key = self.md_pfx % (limit,limit+self.qd_interval)  # key
                temp = float(self.summary[key])                     # PDF
                cdf += temp                                         # CDF
                qd_string += "%.8f\t%.8f\t%.8f\t%.8f\n" % (limit+self.qd_interval/2,temp/qd_num,cdf/qd_num,1-cdf/qd_num) 
                limit += self.qd_interval

            # last interval
            key = self.up_pfx % (self.qd_upper)         # key
            temp = float(self.summary[key])             # PDF
            cdf += temp                                 # CDF
            qd_string += "%.8f\t%.8f\t%.8f\t%.8f\n" % (limit+self.qd_interval/2,temp/qd_num,cdf/qd_num,1-cdf/qd_num)
        
        except Exception, e:
            log = logging.getLogger('agent.stats.get_qd')
            log.error("%s" % e)
        
        return qd_string
        
    #------------------------------------------------------------------------    
            
    def set_stats_summary(self,_id):        
        
        try:
            
            if self.packets[_id][1] == 0:
                self.summary["no_ans"]+=1
            elif self.packets[_id][1] <= self.packets[_id][0]*0.25:
                self.summary["loss_75-100"]+=1
            elif self.packets[_id][1] <= self.packets[_id][0]*0.5:
                self.summary["loss_50-75"]+=1
            elif self.packets[_id][1] <= self.packets[_id][0]*0.75:
                self.summary["loss_25-50"]+=1
            elif self.packets[_id][1] < self.packets[_id][0]:
                self.summary["loss_0-25"]+=1
            elif self.packets[_id][1] == self.packets[_id][0]:
                self.summary["all_rcvd"]+=1
            elif self.packets[_id][1] > self.packets[_id][0]:
                self.summary["rep"]+=1 
                  
            if self.packets[_id][1] == 1:
                self.summary["one_rcvd"]+=1
                
            if self.state_list[_id] != 0 and self.state_list[_id] != -1:
                self.summary["inh"]+=1
                
            if self.average_RTT[_id] > 0 and self.average_RTT[_id] < 0.25:
                self.summary["rtt_0.00-0.25"]+=1
            elif self.average_RTT[_id] > 0.25 and self.average_RTT[_id] < 0.5:
                self.summary["rtt_0.25-0.50"]+=1
            elif self.average_RTT[_id] > 0.5 and self.average_RTT[_id] < 0.75:
                self.summary["rtt_0.50-0.75"]+=1
            elif self.average_RTT[_id] > 0.75 and self.average_RTT[_id] < 1.0:
                self.summary["rtt_0.75-1.00"]+=1
            elif self.average_RTT[_id] > 1.0 and self.average_RTT[_id] < 2.0:
                self.summary["rtt_1.00-2.00"]+=1
            elif self.average_RTT[_id] > 2.0:
                self.summary["rtt_2.00+"]+=1
        
        except Exception, e:
            log = logging.getLogger('agent.stats.set_summary')
            log.error("%s" % e)
