#Target from ip list
class DestList():
    
    def __init__(self):     
        self.full_list = []
        self.type = []
        self.size = 0
        
    def insert(self,addr,is_valid=0):
        self.full_list.append(addr)
        self.size += 1
        
    def remove_last(self):
        try:
            self.full_list.pop()
            self.type.pop()
            self.size = max(self.size-1,0)
        except Exception,e:
            print e
            pass
        
    def activate_all(self):
        for i in range(self.size):
            if self.state_list[i]!=13 and self.state_list[i]!=0:
                self.state_list[i] = 0 
    
    def get_target(self,_id):
        try:
            return self.full_list[_id]
        except:
            pass
        
    def reset(self):
        self.full_list = []
        self.type = []
        self.size = 0
