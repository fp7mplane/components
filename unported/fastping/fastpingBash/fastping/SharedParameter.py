import sys,logging,socket
from threading          import Condition

class SharedParameter():
 
    def __init__(self,Parameters=None,Socket=None,Stats=None,Hostname=None):
        self.parameters=Parameters        
        self.socket=Socket
        self.stats=Stats
        self.hostname=Hostname
         
        self.destList=None 
        self.sender=None
        self.receiver=None
        self.uploader=None
        self.finishCycle=False
        self.kill_received=False  
        self.condition= Condition()
        self.uploaderCondition = Condition()

    def check_killed(self,name,event):
        if event.is_set():
            log = logging.getLogger('agent.ping_interrupt')
            log.info("%s receiving Keyboard Interrupt" % name)               
            try:
                self.condition.acquire()         
                if self.socket is not None: #control if it is close and find the code          
                    try:  
                        self.socket.shutdown(socket.SHUT_RDWR) # SHUT_RD=0 , SHUT_WR=1 , SHUT_RDWR=2
                    #except OSError as exc : #I have to upload to python 3.3 and after change next lines 
                    except socket.error as exc: #---> skip error
                       #print ('shutdown  os error  %s' % str (exc))
                       exc #bug python, there is and error, but the socket is closed in a good way
                    self.socket.close()                                
                    self.socket = None     
                print name+": Killed"
                sys.exit(0)
            except Exception, e:
                log.error("Failures, killing the process" % e)
            finally:
                self.condition.notify()        
                self.condition.release()
                


