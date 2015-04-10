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
            # s = ftplib.FTP(cfg['FTP_SERVER'], cfg['USERNAME'], cfg['PASSWORD'])
            s = ftplib.FTP()
            s.connect(self.shared.parameters.ftp_server,self.shared.parameters.port)     #specify port number when connection
            s.login(self.shared.parameters.user,self.shared.parameters.pwd)
            s.set_pasv(self.shared.parameters.is_pasv)
            s.cwd(self.shared.parameters.curr_dir)
            
        except Exception, why:
            for filename in filenames:
                err[filename] = "Could not connect to FTP server: %s" % why
            return err

        for filename in filenames:
            fp = None
            try:
                print "result: "+os.path.basename(filename)
                 
                fp = open(filename, 'rb')
                s.storbinary('STOR %s' % os.path.basename(filename), fp)
            except Exception, why:
                err[filename] = "Error uploading file %s: " % why
            finally:
                if fp: fp.close()

        try:
            s.quit()
        except Exception, why:
            s.close()

        return err
