#!/usr/bin/env python

import sys,argparse,os,urllib
from datetime import datetime

sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/fastping/')
from Fastping import Fastping

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
       raise argparse.ArgumentTypeError("The file %s does not exist!"%arg)
    else:
       return os.path.abspath(arg)  #return an open file handle

def check_positive(parser, arg):
    ivalue = int(arg)
    if ivalue <= 0 and ivalue != -1: #add not -1
         raise argparse.ArgumentTypeError("Cycle number should be positive or -1: %d" %ivalue)
    return ivalue

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='------------Fastping tool------------')

    #Manager cycle setting
    parser.add_argument('-d','--deltaM',type=int,default=300,help='cycle duration')#default 300
    parser.add_argument('-f','--freqPing',type=float,default=1,help='frequency of ping for each destination') 
    parser.add_argument('-n','--numberCycle',type=lambda x: check_positive(parser,x),default=1,help='Number of cycles, -1 continuous measurements') 

#CycleSetting 
    group = parser.add_mutually_exclusive_group(required=True) 
    group.add_argument('-t','--targetList',nargs='+',help='Target IP list') 
    group.add_argument('-T','--targetFile',type=lambda x: is_valid_file(parser,x),help='file path with destination ip') 
    group.add_argument('-l','--linkFile',type=str,help='Url with destination ip') 
    parser.add_argument('-r','--range',type=int,nargs=2,default=[0,-1],help='lower index, upper index for address range, -1 no upper limit') 

#FolderSetting
    parser.add_argument('-p','--filePath',type=str,default=os.path.dirname(os.path.realpath(__file__))+'/',help='path for output file')
    parser.add_argument('-R','--saveRW', action='store_true',help='Output file Raw statistic')
    parser.add_argument('-Q','--saveQD', action='store_true',help='Output file Queuing delay')
    parser.add_argument('-C','--saveSM', action='store_true',help='Output file Cycle summary')
    parser.add_argument('-S','--saveST', action='store_true',help='Output file Statistic for each destination')
    parser.add_argument('-U','--upload', nargs=6,help='Upload result on server[add more options]')

#Queuing delay setting
    parser.add_argument('-q','--queuingDelay',type=float,nargs=3,default=[0,2,0.01],help='Queuing delay:lower, upper, interval')
    values = parser.parse_args()

    target=values.filePath+"iplist.dat" #default target

    if values.targetFile!=None:
        target=values.targetFile 
    elif values.targetList!=None: 
        try:
            targetFile = open(target,'w')
            for element in values.targetList:
                targetFile.write(element+'\n')
        except Exception, why:
            print "Exception write destination:"
            print why
            sys.exit()        
        finally:
            if targetFile: targetFile.close()
    elif values.linkFile!=None:
        try:
            urllib.urlretrieve (values.linkFile, target)
        except Exception, why:
            print why  
            sys.exit()
    upload=False
    if values.upload!=None:
        upload=True
    print "deltaM:{0:d}\tfreqPing:{1:2f}\tnumberCycle:{2:d}\ttarget:{3:s}\trange:{4:s}\tfilePath:{5:s}\tsaveRW:{6:}\tsaveQD:{7:}\tsaveSM:{8:}\tsaveST:{9:}\tUpload:{10:}\tqueuingDelay:{11:s}\n".format(values.deltaM,values.freqPing,values.numberCycle,target,values.range,values.filePath,values.saveRW,values.saveQD,values.saveSM,values.saveST,values.upload,values.queuingDelay)

    fast=Fastping  (values.deltaM,values.freqPing,values.numberCycle,target,values.range,values.filePath,values.saveRW,values.saveQD,values.saveSM,values.saveST,values.upload,values.queuingDelay)
    print "Time: "+str(datetime.utcnow())
    fast.run()
print "Time: "+str(datetime.utcnow())
