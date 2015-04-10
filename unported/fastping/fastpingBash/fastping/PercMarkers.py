
import logging

class PercMarkers():
    
    def __init__(self,_P):
        
        self.p = _P
        self.q = []
        self.n = []
        self.n_des = []
        self.dn = []
        self.num = 0
        self.p_size = 0
        
        # CREATE MARKERS
        for p in self.p:
            self.q.append([-1,-1,-1,-1,-1])
            self.n.append([1.0,2.0,3.0,4.0,5.0])
            self.n_des.append([1, 1+2*p, 1+4*p, 3+2*p, 5])
            self.dn.append([0, p/2, p, (1+p)/2, 1])
            self.p_size += 1
  
    #------------------------------------------------------------------------

    def add_value(self,_x):
        
        # SAVE FIRST 5 VALUES
        if self.num < 5:
            for p in range(self.p_size):
                self.q[p][self.num] = _x
                
            self.num += 1
            
            # SORT FIRST 5 VALUES
            if self.num == 5:
                for q in self.q:
                    q.sort()
                
        else:
            
            # FIND CELL 'K' CONTAINING ACTUAL VALUE 
            for p in range(self.p_size):
                k = 0
                if _x < self.q[p][0]:
                    self.q[p][0] = _x
                    k = 0
                elif self.q[p][0] <= _x and _x < self.q[p][1]:
                    k = 1
                elif self.q[p][1] <= _x and _x < self.q[p][2]:
                    k = 2
                elif self.q[p][2] <= _x and _x < self.q[p][3]:
                    k = 3
                elif self.q[p][3] <= _x and _x < self.q[p][4]:
                    k = 4
                else:
                    self.q[p][4] = _x
                    k = 4
                    
                # UPDATE MARKERS POSITION
                for i in range(k,5):
                    self.n[p][i] += 1
                        
                for i in range(0,5):
                    self.n_des[p][i] += self.dn[p][i]
                        
                # ADJUST MARKERS 2-3-4
                for i in range(1,4):
                    di = self.n_des[p][i] - self.n[p][i]
                    if (di>=1 and self.n[p][i+1]-self.n[p][i]>1) or (di<=-1 and self.n[p][i-1]-self.n[p][i]<-1):
                            
                        # get sign(d)
                        if di>0:
                            di = 1
                        else:
                            di = -1
                            
                        # P2 predition
                        qi = self.q[p][i] + (di/(self.n[p][i+1]-self.n[p][i-1])) * ((self.n[p][i]-self.n[p][i-1]+di)*(self.q[p][i+1]-self.q[p][i])/(self.n[p][i+1]-self.n[p][i]) + (self.n[p][i+1]-self.n[p][i]-di)*(self.q[p][i]-self.q[p][i-1])/(self.n[p][i]-self.n[p][i-1]))      
                        if self.q[p][i-1] < qi or qi > self.q[p][i+1]:
                            self.q[p][i] = qi                                                                               # P2 predition
                        else:               
                            self.q[p][i] = self.q[p][i] + di*(self.q[p][i+di]-self.q[p][i])/(self.n[p][i+di]-self.n[p][i])  # linear predition
                        self.n[p][i] += di 
                          
    #------------------------------------------------------------------------
                
    def get_perc(self,_p=None):
        try:
            if _p == None:
                temp = []
                for q in self.q:
                    temp.append(q[2])
                return temp
            else:
                return self.q[_p][2]
            
        except IndexError, e:
            log = logging.getLogger('agent.markers.get_perc')
            log.error("%s" % e)
            
    #------------------------------------------------------------------------
    
    def toString(self):
        temp = ""
        for q in self.q:
            temp += "%.8e\t" % q[2]
        return temp
