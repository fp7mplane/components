#!/usr/bin/python
# -*- coding: utf-8 -*-

#from Config.TopHat      import cfg
#from tools              import Tool


import ftplib, os.path

class UploadOPT():
    def call(self, filenames,shared):
        self.shared=shared
        if not isinstance(filenames, list):
            filenames = [filenames]
        err = {}

        try:
            
            print self.shared.parameters.ftp_server
            print self.shared.parameters.port
            print self.shared.parameters.user
            print self.shared.parameters.pwd
            # s = ftplib.FTP(cfg['FTP_SERVER'], cfg['USERNAME'], cfg['PASSWORD'])
            s = ftplib.FTP()
            s.connect(self.shared.parameters.ftp_server,self.shared.parameters.port)     #specify port number when connection
            s.login(self.shared.parameters.user,self.shared.parameters.pwd)
            s.set_pasv(self.shared.parameters.is_pasv)
            try:
                s.mkd(shared.parameters.curr_dir)
            except: pass
            s.cwd(shared.parameters.curr_dir)
            
        except Exception, why:
            for filename in filenames:
                err[filename] = "Error: Could not connect to FTP server: %s" % why
            print  err[filename]
            return err
        try:
            for filename in filenames:
                #fp = None
                print "result: "+os.path.basename(filename)
                fp = open(filename, 'rb')
                s.storbinary('STOR %s' % os.path.basename(filename), fp)
        except Exception, why:
            err[filename] = "Error: uploading file %s: " % why
            print  "Error: "+err[filename]
        finally:
            if fp: fp.close()

        try:
            s.quit()
        except Exception, why:
            s.close()

        return err
