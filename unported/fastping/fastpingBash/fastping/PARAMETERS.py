class Parameters():
   
    def __init__(self,deltaM=10,ping_freq=1,MAX_CYCLE=1,target="iplist.dat",lowerUpper=[0,-1],filepath="./fastpingBash/",saveRaw=True,saveCycleSummary=False,saveStat=False,saveQD=False,upload=False,queuingDelay=[0.0,2.0,0.01],ftp=["127.0.0.1","anonymous","",21,"up",False]):
     #-----------------------------------------------   
        # SERVER SETTINGS   
	"""
        self.ftp_server = "mplanethesis.polito.it"
        self.user       = "paristech"
        self.pwd        = "Baghett%"
        self.port       = 2021
        self.curr_dir   = "MPLANEANYCAST"
        self.is_pasv    = False
	
 
                   
        self.ftp_server = "127.0.0.1"
        self.user       = "anonymous"
        self.pwd        = ""
        self.port       = 21
        self.curr_dir   = "up"
        self.is_pasv    = False      
    """    
        self.ftp_server = ftp[0]
        self.user       = ftp[1]
        self.pwd        = ftp[2]
        self.port       = ftp[3]
        self.curr_dir   = ftp[4]
        self.is_pasv    = ftp[5]      
        
#-----------------------------------------------
        # MANAGER SETTINGS
        self.MANAGER_DEFAULTS = {"delta_M"   : deltaM,   # in seconds 300
                                 "ping_freq" : ping_freq,
                                 "MAX_CYCLE" : MAX_CYCLE}
        # WORKING CYCLE SETTINGS
        self.CYCLE_DEFAULTS = {"iplist_file" : target,                                                # list of destinations for PLANETLAB
                               "LOWER_LIMIT" : lowerUpper[0],                                                                            # min target ID [included]
                               "UPPER_LIMIT" : lowerUpper[1]}                                                                                  # max target ID [not included]
        # FOLDERS
        self.filePath=filepath
        self.RAW_DIR    = self.filePath+"archive/"
        self.STATS_DIR  = self.filePath+"stats/"
        self.SAVE_RW = saveRaw        
        self.SAVE_SM=saveCycleSummary
        self.SAVE_ST=saveStat
        self.SAVE_QD=saveQD
        self.Upload=upload
        self.log=self.filePath+"fastping.log"    
        # QUEUING DELAY [seconds]
        self.qd_lower = queuingDelay[0]
        self.qd_upper = queuingDelay[1]
        self.qd_interval = queuingDelay[2]
        self.qd_cyphers = len(str(self.qd_interval))-2
        self.packet_size=58

