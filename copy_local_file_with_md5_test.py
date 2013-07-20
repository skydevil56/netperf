#!/usr/bin/python
import os
import hashlib
import time
import sys, getopt
import re
import warnings
import subprocess as sp
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko

LocalFile = '/root/test_loc_file'
RemoteFile = '/root/test_remote_file'
# LSP
first_site_lsp_IMIT ='/root/first_site_lsp_IMIT'
first_site_lsp_CI ='/root/first_site_lsp_CI'
first_site_lsp_C ='/root/first_site_lsp_C'
second_site_lsp_C_CI_IMIT = '/root/second_site_lsp_C_CI_IMIT'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def PutLocalFileToRemoteHost (RemoteHostIP, Port, Username, Password, LocalFile, RemoteFile):
    if os.path.isfile(LocalFile): # check to exitst of local file
        print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Local file: " + str(LocalFile) + " exists"
        hash_of_local_file = MD5Checksum (LocalFile) # calculate hash of local file
        print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " MD5 hash: " + str(hash_of_local_file) + " of local file: " + str(LocalFile)
        try:
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            sftp = s.open_sftp()
            try:
                sftp.stat(RemoteFile)
            except IOError:
                print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Remote file: " + str (RemoteFile) + " on host: " + str (RemoteHostIP) + " does't not exist"
                try:
                    sftp.put(LocalFile, RemoteFile) # if file does't exist on remote host copy local file to remote host
                except IOError:
                    sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " Can't copy file: " + str(LocalFile) + " to remote host: " + str(RemoteHostIP))
                else:
                    print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Local file: " + str (LocalFile) + " was copy to host: " + str (RemoteHostIP) + " its name: " + str(RemoteFile)
                    return 0
            else:
                print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Remote file: " + str (RemoteFile) + " on host: " + str (RemoteHostIP) + " exist"
                temp_remote_file_on_local_host = os.path.join(os.path.dirname(RemoteFile), "temp_" + os.path.basename(RemoteFile)) # create temp_ suffix for remote file that copy it on local host to calculate md5 hash
                print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Name of temp file (for remote file) is: " + str (temp_remote_file_on_local_host)
                sftp.get(RemoteFile, temp_remote_file_on_local_host) # get remote file to local host
                hash_of_temp_remote_file = MD5Checksum(temp_remote_file_on_local_host) # calculate md5 hash for temp file
                print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " MD5 hash: " + str(hash_of_temp_remote_file) + " of temp local file: " + str(temp_remote_file_on_local_host) + " from remote host: " + str(RemoteHostIP)
                if hash_of_local_file == hash_of_temp_remote_file:
                    print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " MD5 hashs of: " + str(temp_remote_file_on_local_host) + " and: " + str(LocalFile) + " are same"
                    os.remove(temp_remote_file_on_local_host) # if remote and local files are same - del temp file
                    print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Temp file (for remote file): " + str (temp_remote_file_on_local_host) + " was deleted"
                    return 0
                else:
                    if hash_of_local_file != hash_of_temp_remote_file: # if remote and local files are not same
                        print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " MD5 hashs of: " + str(temp_remote_file_on_local_host) + " and: " + str(LocalFile) + " are not same"
                        try:
                            sftp.remove(RemoteFile)
                        except:
                            sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " Can't remove file: " + str(RemoteFile) + " from remote host: " +str(RemoteHostIP))
                        else:
                            print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Remote file: " + str (RemoteFile) + " on host: " + str (RemoteHostIP) + " was deleted"
                            os.remove(temp_remote_file_on_local_host)
                            print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Temp file (for remote file): " + str (temp_remote_file_on_local_host) + " was deleted"
                            sftp.put(LocalFile, RemoteFile)
                            print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Local file: " + str(LocalFile) + " was copy to host: " + str(RemoteHostIP) + " its name: " + str(RemoteFile)
                            return 0
        finally:
            s.close()
    else:
        sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " Local file: " + str(LocalFile) + " does't exists")



def MD5Checksum(FilePath):
    try:
        file = open(FilePath, 'rb')
    except IOError:
        sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " Can't open local file: " + str(FilePath))
    else:
        m = hashlib.md5() # create new hashlib obj
        while True:
            data = file.read(8192)
            if not data:
                break
            else:
                m.update(data) # recalculate hash (data + data + data + ...)
        return m.hexdigest() # return hash of file
    finally:
        file.close()

def ChangeLSPRemoteOnSterraGate (RemoteHostIP, Port, Username, Password, RemoteLSP):
        try:
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            check_lsp = 'lsp_mgr check -f ' + str(RemoteLSP)
            print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Check LSP command: " + str(check_lsp)
            stdin, stdout, stderr = s.exec_command(check_lsp)
            status = stdout.channel.recv_exit_status()
            if status != 0:
                sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " Can't check LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP))
            else:
                if status == 0:
                    print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Check LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP) + " was successful"
                    load_lsp = 'lsp_mgr load -f ' + str(RemoteLSP)
                    stdin, stdout, stderr = s.exec_command(load_lsp)
                    status = stdout.channel.recv_exit_status()
                    if status !=0:
                        sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " Can't load LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP))
                    else:
                        if status == 0:
                            print bcolors.OKGREEN + "Info: " + bcolors.ENDC + " Load LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP) + " was successful"

        return 0

def PutLSPToRemoteHost (FirsSiteIP, SecondSiteIP, Port, Username, Password):
    # Put to First site
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, first_site_lsp_IMIT, first_site_lsp_IMIT)
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, first_site_lsp_CI, first_site_lsp_CI)
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, first_site_lsp_C, first_site_lsp_C)
    # Put to Second site
    PutLocalFileToRemoteHost (SecondSiteIP, Port, Username, Password, second_site_lsp_C_CI_IMIT, second_site_lsp_C_CI_IMIT)
    return 0

PutLSPToRemoteHost ('192.168.7.2', '192.168.8.2', 22, 'root', 'russia')
ChangeLSPRemoteOnSterraGate ('192.168.8.2', 22, 'root', 'russia', second_site_lsp_C_CI_IMIT)
ChangeLSPRemoteOnSterraGate ('192.168.7.2', 22, 'root', 'russia', first_site_lsp_IMIT)
ChangeLSPRemoteOnSterraGate ('192.168.7.2', 22, 'root', 'russia', first_site_lsp_C)
ChangeLSPRemoteOnSterraGate ('192.168.7.2', 22, 'root', 'russia', first_site_lsp_CI)
