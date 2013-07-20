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

port = 22
username = 'root'
password = 'russia'

LocalFileVmstatS1 = '/root/vmstat_s1'
RemoteFileVmstatS1 = '/root/vmstat_s1'
LocalFileVmstatS2 = '/root/vmstat_s2'
RemoteFileVmstatS2 = '/root/vmstat_s2'

LocalFileMpstatS1 = '/root/mpstat_s1'
RemoteFileMpstatS1 = '/root/mpstat_s1'
LocalFileMpstatS2 = '/root/mpstat_s2'
RemoteFileMpstatS2 = '/root/mpstat_s2'

# LSP
first_site_lsp_IMIT ='/root/first_site_lsp_IMIT'
first_site_lsp_CI ='/root/first_site_lsp_CI'
first_site_lsp_C ='/root/first_site_lsp_C'
second_site_lsp_C_CI_IMIT = '/root/second_site_lsp_C_CI_IMIT'

StartMbpsForNuttcp = 1000

UDP1400 = 1400
UDP512 = 512
UDP64 = 64

mpstat_header_regexp = re.compile('[\d]{2}:[\d]{2}:[\d]{2}[\s]{0,}CPU[\s]{0,}%usr[\s]{1,}%nice[\s]{1,}%sys[\s]{1,}%iowait[\s]{1,}%irq[\s]{1,}%soft[\s]{1,}%steal[\s]{1,}%guest[\s]{1,}%idle|^[\s]{1,}|Linux.{0,}[\(][\s]{0,}[\d]{1,}[\s]{1,}CPU[\s]{0,}[\)][\s]{0,}')

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

def CheckStartrRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName):
    # if return status is 0 - remote daemon is now running
    # if return status is 1 - remote daemon is not running
    check_daemon_is_starting = "ps -A | grep " + str(DaemonName)
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(RemoteHostIP, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command(check_daemon_is_starting)
    status = stdout.channel.recv_exit_status()
    if (status != 0) and (status != 1):
        sys.exit("Error in CheckStartrRemoteDaemon status is " + str(status))
    s.close()
    return status

def CheckStartrLocalDaemon (DaemonName):
    # if return status is 0 - local daemon is now running
    # if return status is 1 - local daemon is not running
    daemon_is_start_out = []
    daemon_is_start = sp.Popen("ps -A | grep " + str(DaemonName), shell=True, executable='/bin/bash', stdout=sp.PIPE)
    daemon_is_start_out = daemon_is_start.communicate()[0].splitlines()
    status = daemon_is_start.returncode
    if (status != 0) and (status != 1):
        sys.exit("Error in CheckStartrLocalDaemon status is " + str(status))
    return status

def StartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName, Parametrs = '', OutputFile = ''):
    # if return status is 0 - remote daemon was successfully start
    # if return status is 1 - remote daemon was't start

    # check what remote daemon is't stat
    if CheckStartrRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 0:
        return 1
    else:
        if OutputFile == '':
            start_remote_daemon = str(DaemonName) + " " + str(Parametrs)
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(RemoteHostIP, Port, Username, Password)
            stdin, stdout, stderr = s.exec_command(start_remote_daemon)
            status = stdout.channel.recv_exit_status()
            if (status != 0) and (status != 1):
                sys.exit("Error in StartRemoteDaemon")
            s.close()
            return status
        else:
            if OutputFile != '':
                start_remote_daemon = str(DaemonName) + " " + str(Parametrs) + " > " + str(OutputFile) + " &"
                paramiko.util.log_to_file('paramiko.log')
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(RemoteHostIP, Port, Username, Password)
                stdin, stdout, stderr = s.exec_command(start_remote_daemon)
                status = stdout.channel.recv_exit_status()
                if (status != 0) and (status != 1):
                    sys.exit("Error in StartRemoteDaemon")
                s.close()
                return status
    return

def StartLocalDaemon (DaemonName, Parametrs = '', OutputFile = ''):
    # if return status is 0 - local daemon was successfully start
    # if return status is 1 - local daemon was't start (daemon already start or incorrect daemon name)

    # check what local daemon is't stat
    if CheckStartrLocalDaemon (DaemonName) == 0:
        return 1
    else:
        if OutputFile == '':
            daemon_start_out = []
            start_daemon = str(DaemonName) + " " + str(Parametrs)
            daemon_is_start = sp.Popen(start_daemon, shell=True, executable='/bin/bash', stdout=sp.PIPE)
            daemon_start_out = daemon_is_start.communicate()[0].splitlines()
            status = daemon_is_start.returncode
            if (status != 0) and (status != 1):
                sys.exit("Error in StartLocalDaemon")
            return status
        else:
            if OutputFile != '':
                daemon_start_out = []
                start_local_daemon = str(DaemonName) + " " + str(Parametrs) + " > " + str(OutputFile) + " &"
                daemon_is_start = sp.Popen(start_local_daemon, shell=True, executable='/bin/bash', stdout=sp.PIPE)
                daemon_start_out = daemon_is_start.communicate()[0].splitlines()
                status = daemon_is_start.returncode
                if (status != 0) and (status != 1):
                    sys.exit("Error in StartLocalDaemon")
                return status
    return

def StopRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName):
    # if return status is 0 - remote daemon is stop
    # if return status is 1 - remote daemon already not running

    # check what remote daemon is start
    if CheckStartrRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 0:
        stop_remote_daemon = "killall " + str(DaemonName)
        paramiko.util.log_to_file('paramiko.log')
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        s.connect(RemoteHostIP, Port, Username, Password)
        stdin, stdout, stderr = s.exec_command(stop_remote_daemon)
        status = stdout.channel.recv_exit_status()
        if status != 0:
            sys.exit("Error in StopRemoteDaemon")
        s.close()
    else:
        return 1
    return status

def StopLocalDaemon (DaemonName):
    # if return status is 0 - local daemon is stop
    # if return status is 1 - local daemon already not running

    # check what local daemon is already start
    if CheckStartrLocalDaemon (DaemonName) == 0:
        daemon_stop_out = []
        stop_local_daemon = "killall " + str(DaemonName)
        daemon_stop = sp.Popen(stop_local_daemon, shell=True, executable='/bin/bash', stdout=sp.PIPE)
        daemon_stop_out = daemon_stop.communicate()[0].splitlines()
        status = daemon_stop.returncode
        if status != 0:
            sys.exit("Error in StopLocalDaemon")
    else:
        return 1
    return status

def RestartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName, Parametrs = '', OutputFile = ''):
    if StopRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 0:
        if StartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName, Parametrs, OutputFile) == 0:
            return 0
        else:
            return 1
    else:
        if StopRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 1:
            if StartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName, Parametrs, OutputFile) == 0:
                return 0
        else:
            return 1
    return

def RestartLocalDaemon (DaemonName, Parametrs = '', OutputFile = ''):
    if StopLocalDaemon (DaemonName) == 0:
        if StartLocalDaemon (DaemonName, Parametrs, OutputFile) == 0:
            return 0
        else:
            return 1
    else:
        if StopLocalDaemon (DaemonName) == 1:
            if StartLocalDaemon (DaemonName, Parametrs, OutputFile) == 0:
                return 0
        else:
            return 1
    return

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

def ParseScriptArguments(argv):
    LocalIP = ''
    RemoteIP = ''
    global Site_1_IP
    global Site_2_IP
    global encryption_algorithm
    global traffc_generator
    encryption_algorithm = ''
    traffc_generator = ''
    Site_1_IP = ''
    Site_2_IP = ''
    IPlist = []
    global LocTrafGenMachineIP
    global RemTrafGenMachineIP
    try:
        opts, args = getopt.getopt(argv,'hL:R:l:r:', ['help', 'ip_local=', 'ip_remote=', 'ip_site1=', 'ip_site2=', 'encr_alg=', 'traf_gen='  ])
    except getopt.GetoptError:
        print
        print bcolors.FAIL + "Error :" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print "Usage: name_of_script.py {options} {parametrs}"
        print "options:"
        print
        print '         --ip_local  IPv4 address    <Local traffic generator machine IP>'
        print '         --ip_remote IPv4 address    <Remote traffic receiver machine IP>'
        print '         --ip_site1  IPv4 address    <First IPsec Site IP> '
        print '         --ip_site2  IPv4 address    <Second IPsec Site IP>'
        print '         --encr_alg  {C | CI | IMIT | ALL}   <Encryption algorithm> '
        print '         --traf_gen  {nuttcp | netperf | ALL}    <Traffic generator>'
        print
        sys.exit()
    if len(opts) == 0:
        print
        print bcolors.FAIL + "Error :" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print "Usage: name_of_script.py {options} {parametrs}"
        print "options:"
        print
        print '         --ip_local  IPv4 address    <Local traffic generator machine IP>'
        print '         --ip_remote IPv4 address    <Remote traffic receiver machine IP>'
        print '         --ip_site1  IPv4 address    <First IPsec Site IP> '
        print '         --ip_site2  IPv4 address    <Second IPsec Site IP>'
        print '         --encr_alg  {C | CI | IMIT | ALL}   <Encryption algorithm> '
        print '         --traf_gen  {nuttcp | netperf | ALL}    <Traffic generator>'
        print
        sys.exit()
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print
            print "Usage: name_of_script.py {options} {parametrs}"
            print "options:"
            print
            print '         --ip_local  IPv4 address    <Local traffic generator machine IP>'
            print '         --ip_remote IPv4 address    <Remote traffic receiver machine IP>'
            print '         --ip_site1  IPv4 address    <First IPsec Site IP> '
            print '         --ip_site2  IPv4 address    <Second IPsec Site IP>'
            print '         --encr_alg  {C | CI | IMIT | ALL}   <Encryption algorithm> '
            print '         --traf_gen  {nuttcp | netperf | ALL}    <Traffic generator>'
            print
            sys.exit()
        elif opt in ('--ip_local'):
            LocTrafGenMachineIP = arg
            IPlist.append(LocTrafGenMachineIP)
        elif opt in ('--ip_remote'):
            RemTrafGenMachineIP = arg
            IPlist.append(RemTrafGenMachineIP)
        elif opt in ('--ip_site2'):
            Site_2_IP = arg
            IPlist.append(Site_2_IP)
        elif opt in ('--ip_site1'):
            Site_1_IP = arg
            IPlist.append(Site_1_IP)
        elif opt in ('--encr_alg'):
            encryption_algorithm = arg
        elif opt in ('--traf_gen'):
            traffc_generator = arg
    if (LocTrafGenMachineIP == '') or (RemTrafGenMachineIP == '') or (Site_1_IP == '') or (Site_2_IP == '') or (encryption_algorithm == '') or (traffc_generator == ''):
        print
        print bcolors.FAIL + "Error :" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print "Usage: name_of_script.py {options} {parametrs}"
        print "options:"
        print
        print '         --ip_local  IPv4 address    <Local traffic generator machine IP>'
        print '         --ip_remote IPv4 address    <Remote traffic receiver machine IP>'
        print '         --ip_site1  IPv4 address    <First IPsec Site IP> '
        print '         --ip_site2  IPv4 address    <Second IPsec Site IP>'
        print '         --encr_alg  {C | CI | IMIT | ALL}   <Encryption algorithm> '
        print '         --traf_gen  {nuttcp | netperf | ALL}    <Traffic generator>'
        print
        sys.exit()
    print 'Local IP is: ', LocTrafGenMachineIP
    print 'Remote IP is: ', RemTrafGenMachineIP
    print 'Site_1 IP is: ', Site_1_IP
    print 'Site_2 IP is: ', Site_2_IP
    print 'Encryption algorithm is:', encryption_algorithm
    print 'Traffic generator is:', traffc_generator
    print
    return IPlist

def PutLSPToRemoteHost (FirsSiteIP, SecondSiteIP, Port, Username, Password):
    # Put to First site
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, first_site_lsp_IMIT, first_site_lsp_IMIT)
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, first_site_lsp_CI, first_site_lsp_CI)
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, first_site_lsp_C, first_site_lsp_C)
    # Put to Second site
    PutLocalFileToRemoteHost (SecondSiteIP, Port, Username, Password, second_site_lsp_C_CI_IMIT, second_site_lsp_C_CI_IMIT)
    return 0

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

def PingTestForIPlist (IPlist):
    number_of_reachable_ip = 0
    if len(IPlist) == 0:
        print bcolors.FAIL + "Error :" + bcolors.ENDC + " PingTestForIPlist(IPlist), IPlist is Null"
    if len(IPlist) == 1:
        ping = sp.Popen("ping -c 1 -w 1 " + str(IPlist[0]), shell=True, executable='/bin/bash', stdout=sp.PIPE)
        PingOtputs = ping.communicate()[0]
        status = ping.returncode
        return status
    if len(IPlist) > 1:
        for IP in IPlist:
            ping = sp.Popen("ping -c 1 -w 1 " + str(IP), shell=True, executable='/bin/bash', stdout=sp.PIPE)
            PingOtputs = ping.communicate()[0]
            status = ping.returncode
            if status == 0:
                number_of_reachable_ip = number_of_reachable_ip +1
            else:
                print bcolors.FAIL + "Error :" + bcolors.ENDC + " IP " + str(IP) + " Unreachable"
                sys.exit()
        if (number_of_reachable_ip == len(IPlist)):
            print "Network test completed successfully"
            print
        else:
            sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " check the network settings")
        print
    return 0

def GetNumberOfProcessorsOnRemoteHost(RemoteHostIP, Port, Username, Password):
    command_for_finding_number_of_processor = 'cat /proc/cpuinfo | grep proc | wc -l'
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(RemoteHostIP, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command(command_for_finding_number_of_processor)
    status = stdout.channel.recv_exit_status()
    if status != 0:
        sys.exit("Error in GetNumberOfProcessorsOnRemoteHost")
    number_of_processor = stdout.read().split()[0]
    s.close()
    return number_of_processor

def GetCpuListForMpstat (NumberOfCPU):
    cpu_list_without_first_core = []
    for i in range(int(NumberOfCPU)):
        # exclude first CPU
        if i != 0:
            cpu_list_without_first_core.append(str(i))
    # make a list in the form of 1,2,3...
    cpu_list_for_mpstat = ','.join(cpu_list_without_first_core)
    return cpu_list_for_mpstat

def GetFilesFromRemoteHost (RemoteHostIP, Port, Username, Password, LocalFile, RemoteFile):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(RemoteHostIP, Port, Username, Password)
    ftp = s.open_sftp()
    ftp.get(LocalFile, RemoteFile)
    s.close()

def NetperfUDP_test (PacketLength, RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = sp.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t UDP_STREAM" + " -i 3,2 " + "-l 20" + " -- " + " -m " + str(PacketLength) + " -M " + str(PacketLength), shell=True, executable='/bin/bash', stdout=sp.PIPE)
    NetperfOtputs = netperf.communicate()[0].splitlines()
    status = netperf.returncode
    if status != 0:
        sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " netperf can't connect to the netserver " + str(RemoteHostIP) + " from " + str(LocalHostIP))
        print
    throughput_max = NetperfOtputs[-3].split()[-1]
    throughput_without_loss = NetperfOtputs[-2].split()[-1]
    return throughput_max, throughput_without_loss

def NetperfTCP_test (RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = sp.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t TCP_STREAM" + " -i 3,2 " + "-l 30", shell=True, executable='/bin/bash', stdout=sp.PIPE)
    NetperfOtputs = netperf.communicate()[0].splitlines()
    status = netperf.returncode
    if status != 0:
        sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " netperf can't connect to the netserver " + str(RemoteHostIP) + " from " + str(LocalHostIP))
        print
    throughput_without_loss = NetperfOtputs[-1].split()[-1]
    return throughput_without_loss

def NuttcpTCP_test (RemoteHostIP):
    IPlist = []
    IPlist.append(RemoteHostIP)
    #flag needs if host reachable via ICMP and returned status != 0 to repeat the test in the last attempts
    flag = 0
    count_of_failed_attempts = 5
    while (1):
        nuttcp = sp.Popen("nuttcp -T 30 " + str(RemoteHostIP), shell=True, executable='/bin/bash', stdout=sp.PIPE)
        # get stdout from nuttcp Otput (stdout, stderr) = nuttcp.communicate()
        nuttcpOtputs = nuttcp.communicate()[0].splitlines()
        status = nuttcp.returncode
        if status != 0:
            if (PingTestForIPlist(IPlist) != 0) and (count_of_failed_attempts > 0):
                print bcolors.WARNING + "WARNING :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the warning: remote host " + str(RemoteHostIP) + " Unreachable"
                print 'Attempts to restore the connection ' + str(count_of_failed_attempts)
                print
                time.sleep(3)
                count_of_failed_attempts = count_of_failed_attempts - 1
                continue
            else:
                if (PingTestForIPlist(IPlist) != 0) and (count_of_failed_attempts <= 0):
                    sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: remote host " + str(RemoteHostIP) + " Unreachable")
                    # if host reachable via ICMP and returned status != 0 repeat the last attempts
                if (PingTestForIPlist(IPlist) == 0) and (flag == 0):
                    flag = 1
                    continue
                else:
                    sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: nuttcp server on the remote host " + str(RemoteHostIP) + " not running")
        else:
            if status == 0:
                break
    speed = nuttcpOtputs[-1].split()[6]
    return speed

def NuttcpUDP_test (Mbps, PacketLength, RemoteHostIP, NumberOfIterations):
    IPlist = []
    IPlist.append(RemoteHostIP)
    min_Mbps_without_loss = 0
    max_Mbps_with_loss = 0
    max_speed_without_loss = 0
    tests_with_loss = 0
    i = NumberOfIterations
    count_of_failed_attempts = 5
    # flag needs if host reachable via ICMP and returned status != 0 to repeat the test in the last attempts
    flag = 0
    while i != 0:
        nuttcp = sp.Popen("nuttcp -u -T 20" + " -Ri " + str(Mbps) + "M" + " -l " + str(PacketLength) + " " + str(RemoteHostIP), shell=True, executable='/bin/bash', stdout=sp.PIPE)
        # get stdout from nuttcp Otput (stdout, stderr) = nuttcp.communicate()
        nuttcpOtputs = nuttcp.communicate()[0].splitlines()
        status = nuttcp.returncode
        if status != 0:
            if (PingTestForIPlist(IPlist) != 0) and (count_of_failed_attempts > 0):
                print bcolors.WARNING + "WARNING :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the warning: remote host " + str(RemoteHostIP) + " Unreachable"
                print 'Attempts to restore the connection ' + str(count_of_failed_attempts)
                print
                time.sleep(3)
                count_of_failed_attempts = count_of_failed_attempts - 1
                continue
            else:
                if (PingTestForIPlist(IPlist) != 0) and (count_of_failed_attempts <= 0):
                    sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: remote host " + str(RemoteHostIP) + " Unreachable")
                # if host reachable via ICMP and returned status != 0 repeat the last attempts
                if (PingTestForIPlist(IPlist) == 0) and (flag == 0):
                    flag = 1
                    continue
                else:
                    sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: nuttcp server on the remote host " + str(RemoteHostIP) + " not running")
        speed_without_loss = nuttcpOtputs[-1].split()[6]
        loss_of_current_test = nuttcpOtputs[-1].split()[-2]

##       if (float(speed_without_loss) > float(max_speed_without_loss) ) and (float(loss_of_current_test) < 1):
##            max_speed_without_loss = speed_without_loss
        if (float(speed_without_loss) > float(max_speed_without_loss) ):
            max_speed_without_loss = speed_without_loss

##        print "Number of test is ", i
##        print "MBps is ", Mbps
##        print "speed is", speed_without_loss
##        print "loss is", loss_of_current_test
##        print "max_speed_without_loss ", max_speed_without_loss
##        print
        if float(loss_of_current_test) > 1:
            tests_with_loss = tests_with_loss + 1
            max_Mbps_with_loss = Mbps
            Mbps = (float(Mbps) + float(min_Mbps_without_loss)) / 2
        else:
            min_Mbps_without_loss = Mbps
            Mbps = (float(Mbps) + float(max_Mbps_with_loss)) / 2
        i = i - 1
##    if tests_with_loss == NumberOfIterations:
##        sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " nuttcp can't find throughput without loss")
    return speed_without_loss, loss_of_current_test, max_speed_without_loss

def ParsingMpstatOutput (MpstatFile,RegExp):
    cpu_idle =[]
    cpu_load = []
    true_cpu_load = []
    mpstat_out_after_not_match_regexp = []
    #open Mpstat output files
    file = open(MpstatFile, 'r')
    mpstat_out = file.readlines()
    #create new list without mpstat header
    for line in mpstat_out:
        if not RegExp.match(line):
            mpstat_out_after_not_match_regexp.append(line)
    #create list with CPU idle values
    for line in mpstat_out_after_not_match_regexp:
        #fix bug in mpstat output, when %idle and %sys have same zero value
        if (float(line.split()[4]) != 0 ) and (float(line.split()[-1]) != 0):
            #parsing CPU (numbers) load and add their to list
            cpu_idle.append(float(line.split()[-1]))
    #create list with CPU load values
    for idle in cpu_idle:
        cpu_load.append(float(100.0 - float(idle)))
    #delete zeros and ones
    if cpu_load.count(0.0) != 0:
        count_zeros = cpu_load.count(0.0)
        for i in range(count_zeros):
            cpu_load.remove(0.0)
    if cpu_load.count(1.0) != 0:
        count_ones = cpu_load.count(1.0)
        for i in range(count_ones):
            cpu_load.remove(1.0)
    #find approximate average of CPU load
    if len(cpu_load) == 0:
        return 0
    avg = float(sum(cpu_load))/float(len(cpu_load))
    #create new list where items > approximate average
    for i in cpu_load:
        if i >= avg:
            true_cpu_load.append(i)
    return float(sum(true_cpu_load))/float(len(true_cpu_load))

def ParsingVmstatOutput (LocalFile):
    vmstat_out =[]
    cpu_load = []
    true_cpu_load =[]
    # open file with Vmstat output
    file = open(LocalFile, 'r')
    vmstat_out = file.readlines()
    #head not read
    for line in vmstat_out[3:-1:]:
        #parsing CPU (numbers) load and add their to list
        cpu_load.append(float(line.split()[13]))
    #delete zeros and ones
    if cpu_load.count(0.0) != 0:
        count_zeros = cpu_load.count(0.0)
        for i in range(count_zeros):
            cpu_load.remove(0.0)
    if cpu_load.count(1.0) != 0:
        count_ones = cpu_load.count(1.0)
        for i in range(count_ones):
            cpu_load.remove(1.0)
    #find approximate average of CPU load
    if len (cpu_load) == 0:
        return 0
    avg = float(sum(cpu_load))/float(len(cpu_load))
    #create new list where items > approximate average
    for i in cpu_load:
        if i >= avg:
            true_cpu_load.append(i)
    return float(sum(true_cpu_load))/float(len(true_cpu_load))

def GeneralNuttcpfUDPTestWithMpstat (PacketLength, RemoteHostIP, NumberOfIterations):
    list_of_results_speed = []
    list_of_results_loss = []
    #Start Mpstat
    RestartRemoteDaemon(Site_1_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_1_IP, port, username, password))), RemoteFileMpstatS1)
    RestartRemoteDaemon(Site_2_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_2_IP, port, username, password))), RemoteFileMpstatS2)
    #Start Nuttcp test
    speed, loss, max_speed_without_loss = NuttcpUDP_test(StartMbpsForNuttcp, PacketLength, RemoteHostIP, NumberOfIterations)
    print
    print bcolors.HEADER + "Nuttcp UDP test with Mpstat, PacketLength is " + str(PacketLength) + bcolors.ENDC
    print speed, "Throughput"
    print loss, "Loss"
    #Stop Mmstat
    StopRemoteDaemon(Site_1_IP, port, username, password, 'mpstat')
    StopRemoteDaemon(Site_2_IP, port, username, password, 'mpstat')
    #Get Mpstat files
    GetFilesFromRemoteHost(Site_1_IP, port, username, password, LocalFileMpstatS1, RemoteFileMpstatS1)
    GetFilesFromRemoteHost(Site_2_IP, port, username, password, LocalFileMpstatS2, RemoteFileMpstatS2)
    #Parse CPU load
    cpu_load_on_site1 = ParsingMpstatOutput(LocalFileMpstatS1, mpstat_header_regexp)
    cpu_load_on_site2 = ParsingMpstatOutput(LocalFileMpstatS2, mpstat_header_regexp)
    print cpu_load_on_site1, "CPU load on Site_1 IP is ", Site_1_IP
    print cpu_load_on_site2, "CPU load on Site_2 IP is ", Site_2_IP
    print
    print "Nuttcp UDP test on repeatability of results"
    for i in range(5):
        speed, loss, max_speed_without_loss_temp = NuttcpUDP_test(max_speed_without_loss, PacketLength, RemoteHostIP, 1)
        print
        print "Nuttcp UDP test with Mpstat, PacketLength is ", PacketLength
        print speed, "Throughput"
        print loss, "Loss"
        list_of_results_speed.append(speed)
        list_of_results_loss.append(loss)
    time.sleep(1)
##    avg_speed = (float(sum(list_of_results_speed)))/(float(len(list_of_results_speed)))
##    avg_loss = (float(sum(list_of_results_loss)))/(float(len(list_of_results_loss)))
    return list_of_results_speed, list_of_results_loss

def GeneralNuttcpUDPTestWithVmstat (PacketLength, RemoteHostIP, NumberOfIterations):
    list_of_results_speed = []
    list_of_results_loss = []
    #Start Vmstat
    RestartRemoteDaemon(Site_1_IP, port, username, password, 'vmstat', '2 -n', RemoteFileVmstatS1)
    RestartRemoteDaemon(Site_2_IP, port, username, password, 'vmstat', '2 -n', RemoteFileVmstatS2)
    #Start Nuttcp test
    speed, loss, max_speed_without_loss = NuttcpUDP_test(StartMbpsForNuttcp, PacketLength, RemoteHostIP, NumberOfIterations)
    print
    print bcolors.HEADER + "Nuttcp UDP test with Vmstat, PacketLength is " + str(PacketLength) + bcolors.ENDC
    print speed, "Throughput"
    print loss, "Loss"
    #Stop Vmstat
    StopRemoteDaemon(Site_1_IP, port, username, password, 'vmstat')
    StopRemoteDaemon(Site_2_IP, port, username, password, 'vmstat')
    #Get Vmstat files
    GetFilesFromRemoteHost(Site_1_IP, port, username, password, LocalFileVmstatS1, RemoteFileVmstatS1)
    GetFilesFromRemoteHost(Site_2_IP, port, username, password, LocalFileVmstatS2, RemoteFileVmstatS2)
    #Parse CPU load
    cpu_load_on_site1 = ParsingVmstatOutput(LocalFileVmstatS1)
    cpu_load_on_site2 = ParsingVmstatOutput(LocalFileVmstatS2)
    print cpu_load_on_site1, "CPU load on Site_1 IP is ", Site_1_IP
    print cpu_load_on_site2, "CPU load on Site_2 IP is ", Site_2_IP
    print
    print "Nuttcp UDP test on repeatability of results"
    for i in range(5):
        speed, loss, max_speed_without_loss_temp = NuttcpUDP_test(max_speed_without_loss, PacketLength, RemoteHostIP, 1)
        print
        print "Nuttcp UDP test with Mpstat, PacketLength is ", PacketLength
        print speed, "Throughput"
        print loss, "Loss"
        print
        list_of_results_speed.append(speed)
        list_of_results_loss.append(loss)
    time.sleep(1)
##    avg_speed = (float(sum(list_of_results_speed)))/(float(len(list_of_results_speed)))
##    avg_loss = (float(sum(list_of_results_loss)))/(float(len(list_of_results_loss)))
    return list_of_results_speed, list_of_results_loss

def GeneralNuttcpTCPTestWithMpstat (RemoteHostIP):
    list_of_results_speed = []
    #Start Mpstat
    RestartRemoteDaemon(Site_1_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_1_IP, port, username, password))), RemoteFileMpstatS1)
    RestartRemoteDaemon(Site_2_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_2_IP, port, username, password))), RemoteFileMpstatS2)
    #Start Nuttcp test
    speed = NuttcpTCP_test(RemoteHostIP)
    print
    print bcolors.HEADER + "Nuttcp TCP test with Mpstat " + bcolors.ENDC
    print speed, "Throughput without loss"
    #Stop Mmstat
    StopRemoteDaemon(Site_1_IP, port, username, password, 'mpstat')
    StopRemoteDaemon(Site_2_IP, port, username, password, 'mpstat')
    #Get Mpstat files
    GetFilesFromRemoteHost(Site_1_IP, port, username, password, LocalFileMpstatS1, RemoteFileMpstatS1)
    GetFilesFromRemoteHost(Site_2_IP, port, username, password, LocalFileMpstatS2, RemoteFileMpstatS2)
    #Parse CPU load
    cpu_load_on_site1 = ParsingMpstatOutput(LocalFileMpstatS1, mpstat_header_regexp)
    cpu_load_on_site2 = ParsingMpstatOutput(LocalFileMpstatS2, mpstat_header_regexp)
    print cpu_load_on_site1, "CPU load on Site_1 IP is ", Site_1_IP
    print cpu_load_on_site2, "CPU load on Site_2 IP is ", Site_2_IP
    print
    return

def GeneralNetperfUDPTestWithMpstat (PacketLength, RemoteHostIP, LocalHostIP):
    list_of_results_speed = []
    list_of_results_loss = []
    #Start Mpstat
    RestartRemoteDaemon(Site_1_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_1_IP, port, username, password))), RemoteFileMpstatS1)
    RestartRemoteDaemon(Site_2_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_2_IP, port, username, password))), RemoteFileMpstatS2)
    #Start Nuttcp test
    MaxSpeed, SpeedWithoutLoss = NetperfUDP_test (PacketLength, RemoteHostIP, LocalHostIP)
    print
    print bcolors.HEADER + "Netperf UDP test with Mpstat, PacketLength is " + str(PacketLength) + bcolors.ENDC
    print MaxSpeed, "Throughput max 10^6bits/sec"
    print SpeedWithoutLoss, "Throughput without loss 10^6bits/sec"
    #Stop Mmstat
    StopRemoteDaemon(Site_1_IP, port, username, password, 'mpstat')
    StopRemoteDaemon(Site_2_IP, port, username, password, 'mpstat')
    #Get Mpstat files
    GetFilesFromRemoteHost(Site_1_IP, port, username, password, LocalFileMpstatS1, RemoteFileMpstatS1)
    GetFilesFromRemoteHost(Site_2_IP, port, username, password, LocalFileMpstatS2, RemoteFileMpstatS2)
    #Parse CPU load
    cpu_load_on_site1 = ParsingMpstatOutput(LocalFileMpstatS1, mpstat_header_regexp)
    cpu_load_on_site2 = ParsingMpstatOutput(LocalFileMpstatS2, mpstat_header_regexp)
    print cpu_load_on_site1, "CPU load on Site_1 IP is ", Site_1_IP
    print cpu_load_on_site2, "CPU load on Site_2 IP is ", Site_2_IP
    print
    time.sleep(1)
    return

def GeneralNetperfTCPTestWithMpstat (RemoteHostIP, LocalHostIP):
    #Start Mpstat
    RestartRemoteDaemon(Site_1_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_1_IP, port, username, password))), RemoteFileMpstatS1)
    RestartRemoteDaemon(Site_2_IP, port, username, password, 'mpstat', "3 -P " + str (GetCpuListForMpstat(GetNumberOfProcessorsOnRemoteHost (Site_2_IP, port, username, password))), RemoteFileMpstatS2)
    #Start Nuttcp test
    MaxSpeed = NetperfTCP_test (RemoteHostIP, LocalHostIP)
    print
    print bcolors.HEADER + "Netperf TCP test with Mpstat " + bcolors.ENDC
    print MaxSpeed, "Throughput max 10^6bits/sec"
    #Stop Mmstat
    StopRemoteDaemon(Site_1_IP, port, username, password, 'mpstat')
    StopRemoteDaemon(Site_2_IP, port, username, password, 'mpstat')
    #Get Mpstat files
    GetFilesFromRemoteHost(Site_1_IP, port, username, password, LocalFileMpstatS1, RemoteFileMpstatS1)
    GetFilesFromRemoteHost(Site_2_IP, port, username, password, LocalFileMpstatS2, RemoteFileMpstatS2)
    #Parse CPU load
    cpu_load_on_site1 = ParsingMpstatOutput(LocalFileMpstatS1, mpstat_header_regexp)
    cpu_load_on_site2 = ParsingMpstatOutput(LocalFileMpstatS2, mpstat_header_regexp)
    print cpu_load_on_site1, "CPU load on Site_1 IP is ", Site_1_IP
    print cpu_load_on_site2, "CPU load on Site_2 IP is ", Site_2_IP
    print
    time.sleep(1)
    return

def ChoseTest (Attempts):
    if (encryption_algorithm == 'C') and (traffc_generator == 'netperf'):
        FullNetperfTestWithMpstat_C (Attempts)
    if (encryption_algorithm == 'CI') and (traffc_generator == 'netperf'):
        FullNetperfTestWithMpstat_CI (Attempts)
    if (encryption_algorithm == 'IMIT') and (traffc_generator == 'netperf'):
        FullNetperfTestWithMpstat_IMIT (Attempts)
    if (encryption_algorithm == 'ALL') and (traffc_generator == 'netperf'):
        FullNetperfTestWithMpstat_ALL (Attempts)
    if (encryption_algorithm == 'C') and (traffc_generator == 'nuutcp'):
        FullNuttcpfTestWithMpstat_C (Attempts)
    if (encryption_algorithm == 'CI') and (traffc_generator == 'nuutcp'):
        FullNuttcpfTestWithMpstat_CI (Attempts)
    if (encryption_algorithm == 'IMIT') and (traffc_generator == 'nuutcp'):
        FullNuttcpfTestWithMpstat_IMIT (Attempts)
    if (encryption_algorithm == 'ALL') and (traffc_generator == 'nuutcp'):
        FullNuttcpfTestWithMpstat_ALL (Attempts)
    if (encryption_algorithm == 'ALL') and (traffc_generator == 'ALL'):
        FullNuttcpfAndNuttcpTestWithMpstat_ALL (Attempts)

def FullNetperfTestWithMpstat_C (Attempts):
        print bcolors.HEADER + "Start test CHIPER with Netpef (Mpstat)" + bcolors.ENDC
        #ChangeLSPRemoteOnSterraGate (Site_2_IP, port, username, password, second_site_lsp_C_CI_IMIT)
        ChangeLSPRemoteOnSterraGate (Site_1_IP, port, username, password, first_site_lsp_C)
        FullNetperfTestWithMpstat(Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNetperfTestWithMpstat_CI (Attempts):
        print bcolors.HEADER + "Start test CHIPER and INTEGRITY with Netpef (Mpstat)" + bcolors.ENDC
        #ChangeLSPRemoteOnSterraGate (Site_2_IP, port, username, password, second_site_lsp_C_CI_IMIT)
        ChangeLSPRemoteOnSterraGate (Site_1_IP, port, username, password, first_site_lsp_CI)
        FullNetperfTestWithMpstat(Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNetperfTestWithMpstat_IMIT (Attempts):
        print bcolors.HEADER + "Start test IMIT with Netpef (Mpstat)" + bcolors.ENDC
        #ChangeLSPRemoteOnSterraGate (Site_2_IP, port, username, password, second_site_lsp_C_CI_IMIT)
        ChangeLSPRemoteOnSterraGate (Site_1_IP, port, username, password, first_site_lsp_IMIT)
        FullNetperfTestWithMpstat(Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNetperfTestWithMpstat_ALL (Attempts):
        print bcolors.HEADER + "Start test ALL with Netpef (Mpstat)" + bcolors.ENDC
        FullNetperfTestWithMpstat_C (Attempts)
        FullNetperfTestWithMpstat_CI (Attempts)
        FullNetperfTestWithMpstat_IMIT (Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.END

def FullNuttcpfTestWithMpstat_C (Attempts):
        print bcolors.HEADER + "Start test CHIPER with Nuttcp (Mpstat)" + bcolors.ENDC
        #ChangeLSPRemoteOnSterraGate (Site_2_IP, port, username, password, second_site_lsp_C_CI_IMIT)
        ChangeLSPRemoteOnSterraGate (Site_1_IP, port, username, password, first_site_lsp_C)
        FullNuttcpTestWithMpstat(Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_CI (Attempts):
        print bcolors.HEADER + "Start test CHIPER and INTEGRITY with Nuttcp (Mpstat)" + bcolors.ENDC
        #ChangeLSPRemoteOnSterraGate (Site_2_IP, port, username, password, second_site_lsp_C_CI_IMIT)
        ChangeLSPRemoteOnSterraGate (Site_1_IP, port, username, password, first_site_lsp_CI)
        FullNuttcpTestWithMpstat(Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_IMIT (Attempts):
        print bcolors.HEADER + "Start test IMIT with Nuttcp (Mpstat)" + bcolors.ENDC
        #ChangeLSPRemoteOnSterraGate (Site_2_IP, port, username, password, second_site_lsp_C_CI_IMIT)
        ChangeLSPRemoteOnSterraGate (Site_1_IP, port, username, password, first_site_lsp_IMIT)
        FullNuttcpTestWithMpstat(Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_ALL (Attempts):
        print bcolors.HEADER + "Start test ALL with Nuttcp (Mpstat)" + bcolors.ENDC
        FullNuttcpfTestWithMpstat_C (Attempts)
        FullNuttcpfTestWithMpstat_CI (Attempts)
        FullNuttcpfTestWithMpstat_IMIT (Attempts)
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfAndNuttcpTestWithMpstat_ALL (Attempts):
        print bcolors.HEADER + "Start test ALL with Nuttcp and Netperf (Mpstat)" + bcolors.ENDC
        FullNuttcpfTestWithMpstat_ALL (Attempts)
        FullNetperfTestWithMpstat_ALL (Attempts)

#Nuttcp test with Mpstat
def FullNuttcpTestWithMpstat (Attempts):
    for attempts in range(1):
        avg_speed_UDP1400, avg_loss_UDP1400 = GeneralNuttcpfUDPTestWithMpstat (1400, RemTrafGenMachineIP, 10)
        avg_speed_UDP1000, avg_loss_UDP1000 = GeneralNuttcpfUDPTestWithMpstat (1000, RemTrafGenMachineIP, 10)
        avg_speed_UDP512, avg_loss_UDP512 = GeneralNuttcpfUDPTestWithMpstat (512, RemTrafGenMachineIP, 10)
        avg_speed_UDP64, avg_loss_UDP64 = GeneralNuttcpfUDPTestWithMpstat (64, RemTrafGenMachineIP, 10)
        GeneralNuttcpTCPTestWithMpstat (RemTrafGenMachineIP)
        print bcolors.HEADER + "Average result for Nuttcp tests" + bcolors.ENDC
        print
        print bcolors.OKBLUE + "UDP1400 speed is" + str(avg_speed_UDP1400) + " loss is " + str(avg_loss_UDP1400) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP1000 speed is" + str(avg_speed_UDP1000) + " loss is " + str(avg_loss_UDP1000) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP512 speed is" + str(avg_speed_UDP512) + " loss is " + str(avg_loss_UDP512) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP64 speed is" + str(avg_speed_UDP64) + " loss is " + str(avg_loss_UDP64) + bcolors.ENDC
        print

#Nuttcp test with Vmstat
def FullNuttcpTestWithVmstat (Attempts):
    for attempt in range(Attempts):
        avg_speed_UDP1400, avg_loss_UDP1400 = GeneralNuttcpUDPTestWithVmstat (1400, RemTrafGenMachineIP, 10)
        avg_speed_UDP1000, avg_loss_UDP1000 = GeneralNuttcpUDPTestWithVmstat (1000, RemTrafGenMachineIP, 10)
        avg_speed_UDP512, avg_loss_UDP512 = GeneralNuttcpUDPTestWithVmstat (512, RemTrafGenMachineIP, 10)
        avg_speed_UDP64, avg_loss_UDP64 = GeneralNuttcpUDPTestWithVmstat (64, RemTrafGenMachineIP, 10)
        print bcolors.HEADER + "Average result for Nuttcp tests" + bcolors.ENDC
        print
        print bcolors.OKBLUE + "UDP1400 speed is" + str(avg_speed_UDP1400) + " loss is " + str(avg_loss_UDP1400) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP1000 speed is" + str(avg_speed_UDP1000) + " loss is " + str(avg_loss_UDP1000) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP512 speed is" + str(avg_speed_UDP512) + " loss is " + str(avg_loss_UDP512) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP64 speed is" + str(avg_speed_UDP64) + " loss is " + str(avg_loss_UDP64) + bcolors.ENDC

#Netperf test with Mpstat
def FullNetperfTestWithMpstat (Attempts):
    for attempt in range(Attempts):
        GeneralNetperfUDPTestWithMpstat (1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
        GeneralNetperfUDPTestWithMpstat (1000, RemTrafGenMachineIP, LocTrafGenMachineIP)
        GeneralNetperfUDPTestWithMpstat (512, RemTrafGenMachineIP, LocTrafGenMachineIP)
        GeneralNetperfUDPTestWithMpstat (64, RemTrafGenMachineIP, LocTrafGenMachineIP)
        GeneralNetperfTCPTestWithMpstat (RemTrafGenMachineIP, LocTrafGenMachineIP)

# get IP addresses
ip_list = ParseScriptArguments(sys.argv[1:])
print "The test is running now, please wait ..."
print
PingTestForIPlist(ip_list)
PutLSPToRemoteHost (Site_1_IP, Site_2_IP, port, username, password)
ChangeLSPRemoteOnSterraGate (Site_2_IP, port, username, password, second_site_lsp_C_CI_IMIT)
ChoseTest (1)

