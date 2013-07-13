#!/usr/bin/python
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

StartMbpsForNuttcp = 1000

UDP1400 = 1400
UDP512 = 512
UDP64 = 64

mpstat_header_regexp = re.compile('[\d]{2}:[\d]{2}:[\d]{2}[\s]{0,}CPU[\s]{0,}%usr[\s]{1,}%nice[\s]{1,}%sys[\s]{1,}%iowait[\s]{1,}%irq[\s]{1,}%soft[\s]{1,}%steal[\s]{1,}%guest[\s]{1,}%idle|^[\s]{1,}|Linux.{0,}[\(][\s]{0,}[\d]{1,}[\s]{1,}CPU[\s]{0,}[\)][\s]{0,}')

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
    Site_1_IP = ''
    Site_2_IP = ''
    IPlist = []
    global LocTrafGenMachineIP
    global RemTrafGenMachineIP
    try:
        opts, args = getopt.getopt(argv,"hL:l:R:r:")
    except getopt.GetoptError:
        print
        print bcolors.FAIL + "Error :" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print 'name_of_script.py -L <Local traffic generator machine IP> -l <First IPsec Site IP> -R <Remote traffic receiver machine IP> -r <Second IPsec Site IP>'
        print
        sys.exit()
    if len(opts) == 0:
        print
        print bcolors.FAIL + "Error :" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print 'name_of_script.py -L <Local traffic generator machine IP> -l <First IPsec Site IP> -R <Remote traffic receiver machine IP> -r <Second IPsec Site IP>'
        print
        sys.exit()
    for opt, arg in opts:
        if opt == '-h':
            print
            print 'name_of_script.py -L <Local traffic generator machine IP> -l <First IPsec Site IP> -R <Remote traffic receiver machine IP> -r <Second IPsec Site IP>'
            print
            sys.exit()
        elif opt in ("-L"):
            LocTrafGenMachineIP = arg
            IPlist.append(LocTrafGenMachineIP)
        elif opt in ("-R"):
            RemTrafGenMachineIP = arg
            IPlist.append(RemTrafGenMachineIP)
        elif opt in ("-r"):
            Site_2_IP = arg
            IPlist.append(Site_2_IP)
        elif opt in ("-l"):
            Site_1_IP = arg
            IPlist.append(Site_1_IP)
    if (LocTrafGenMachineIP == '') or (RemTrafGenMachineIP == '') or (Site_1_IP == '') or (Site_2_IP == ''):
        print
        print bcolors.FAIL + "Error :" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print 'name_of_script.py -L <Local traffic generator machine IP> -l <First IPsec Site IP> -R <Remote traffic receiver machine IP> -r <Second IPsec Site IP>'
        print
        sys.exit()
    print 'Local IP is ', LocTrafGenMachineIP
    print 'Remote IP is ', RemTrafGenMachineIP
    print 'Site_1 IP is ', Site_1_IP
    print 'Site_2 IP is ', Site_2_IP
    print
    return IPlist

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

# get IP addresses
print "The test is running now, please wait ..."
print
ip_list = ParseScriptArguments(sys.argv[1:])
PingTestForIPlist(ip_list)
#Nuttcp test with Mpstat
for attempts in range(1):
##    avg_speed_UDP1400, avg_loss_UDP1400 = GeneralNuttcpfUDPTestWithMpstat (1400, RemTrafGenMachineIP, 10)
##    avg_speed_UDP1000, avg_loss_UDP1000 = GeneralNuttcpfUDPTestWithMpstat (1000, RemTrafGenMachineIP, 10)
##    avg_speed_UDP512, avg_loss_UDP512 = GeneralNuttcpfUDPTestWithMpstat (512, RemTrafGenMachineIP, 10)
##    avg_speed_UDP64, avg_loss_UDP64 = GeneralNuttcpfUDPTestWithMpstat (64, RemTrafGenMachineIP, 10)
    GeneralNuttcpTCPTestWithMpstat (RemTrafGenMachineIP)
##    print bcolors.HEADER + "Average result for Nuttcp tests" + bcolors.ENDC
##    print
##    print bcolors.OKBLUE + "UDP1400 speed is" + str(avg_speed_UDP1400) + " loss is " + str(avg_loss_UDP1400) + bcolors.ENDC
##    print bcolors.OKBLUE + "UDP1000 speed is" + str(avg_speed_UDP1000) + " loss is " + str(avg_loss_UDP1000) + bcolors.ENDC
##    print bcolors.OKBLUE + "UDP512 speed is" + str(avg_speed_UDP512) + " loss is " + str(avg_loss_UDP512) + bcolors.ENDC
##    print bcolors.OKBLUE + "UDP64 speed is" + str(avg_speed_UDP64) + " loss is " + str(avg_loss_UDP64) + bcolors.ENDC
##    print
#Nuttcp test with Vmstat
for attempts in range(0):
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
for attempts in range(1):
##    GeneralNetperfUDPTestWithMpstat (1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
##    GeneralNetperfUDPTestWithMpstat (1000, RemTrafGenMachineIP, LocTrafGenMachineIP)
##    GeneralNetperfUDPTestWithMpstat (512, RemTrafGenMachineIP, LocTrafGenMachineIP)
##    GeneralNetperfUDPTestWithMpstat (64, RemTrafGenMachineIP, LocTrafGenMachineIP)
    GeneralNetperfTCPTestWithMpstat (RemTrafGenMachineIP, LocTrafGenMachineIP)