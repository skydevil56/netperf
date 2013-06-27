#!/usr/bin/python
import time
import sys
import re
import warnings
import subprocess
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko

port = 22
hostname_s1 = '192.168.7.2'
hostname_s2 = '192.168.8.2'
LocTrafGenMachineIP = '192.168.8.1'
RemTrafGenMachineIP = '192.168.7.1'
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

mpstat_file = '/root/mpstat'
mpstat_header_regexp = re.compile('[\d]{2}:[\d]{2}:[\d]{2}[\s]{0,}CPU[\s]{0,}%usr[\s]{1,}%nice[\s]{1,}%sys[\s]{1,}%iowait[\s]{1,}%irq[\s]{1,}%soft[\s]{1,}%steal[\s]{1,}%guest[\s]{1,}%idle|^[\s]{1,}|Linux.{0,}[\(][\s]{0,}[\d]{1,}[\s]{1,}CPU[\s]{0,}[\)][\s]{0,}')

def StartVmstat (Hostname, Port, Username, Password, RemoteFile):
    vmstat_grep = []
    vmstat_pids = []
    start_vmstat = "vmstat 2 -n > " + str(RemoteFile) + " &"
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command('ps -A | grep vmstat')
    vmstat_grep = stdout.readlines()
    for line in vmstat_grep:
        vmstat_pids.append(line.split()[0])
    if len(vmstat_pids) > 0:
        for i in vmstat_pids:
            stdin, stdout, stderr = s.exec_command("kill " + str(i))
        stdin, stdout, stderr = s.exec_command(start_vmstat)
        stdin, stdout, stderr = s.exec_command('ps -A | grep vmstat')
        vmstat_current_pid = stdout.read().split()[0]
    else:
        stdin, stdout, stderr = s.exec_command(start_vmstat)
        stdin, stdout, stderr = s.exec_command('ps -A | grep vmstat')
        vmstat_current_pid = stdout.read().split()[0]
    s.close()
    return vmstat_current_pid

def StopVmstat (Hostname, Port, Username, Password):
    vmstat_grep = []
    vmstat_pids = []
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command('ps -A | grep vmstat')
    vmstat_grep = stdout.readlines()
    for line in vmstat_grep:
        vmstat_pids.append(line.split()[0])
    if len(vmstat_pids) > 0:
        for i in vmstat_pids:
            stdin, stdout, stderr = s.exec_command("kill " + str(i))
    else:
        print "Error in StopVmstat function var vmstat_pids < 0"
        sys.exit()
    s.close()

def GetVmstatFiles (Hostname, Port, Username, Password, LocalFile, RemoteFile):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    ftp = s.open_sftp()
    ftp.get(LocalFile, RemoteFile)
    s.close()

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
    avg = float(sum(cpu_load))/float(len(cpu_load))
    #create new list where items > approximate average
    for i in cpu_load:
        if i > avg:
            true_cpu_load.append(i)
    return float(sum(true_cpu_load))/float(len(true_cpu_load))

def GetNumberOfProcessorsOnRemoteHost(Hostname, Port, Username, Password):
    command_for_finding_number_of_processor = 'cat /proc/cpuinfo | grep proc | wc -l'
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command(command_for_finding_number_of_processor)
    number_of_processor = stdout.read().split()[0]
    s.close()
    return number_of_processor

def ParsingMpstatOutput (MpstatFile,RegExp):
    cpu_idle =[]
    cpu_load = []
    true_cpu_load = []
    mpstat_out_after_not_match_regexp = []
    file = open(MpstatFile, 'r')
    mpstat_out = file.readlines()
    for line in mpstat_out:
        if not RegExp.match(line):
            mpstat_out_after_not_match_regexp.append(line)
    #head not read
    for line in mpstat_out_after_not_match_regexp[2:-1:]:
        #parsing CPU (numbers) load and add their to list
        cpu_idle.append(float(line.split()[-1]))
    for idle in cpu_idle:
        cpu_load.append(float(100.0 - float(idle)))
    print "before ", cpu_load
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
    avg = float(sum(cpu_load))/float(len(cpu_load))
    print "Average ", avg
    #create new list where items > approximate average
    for i in cpu_load:
        if i > avg:
            true_cpu_load.append(i)
    return float(sum(true_cpu_load))/float(len(true_cpu_load))

def GetCpuListForMpstat (NumberOfCPU):
    cpu_list_without_first_core = []
    for i in range(int(NumberOfCPU)):
        # exclude first CPU
        if i != 0:
            cpu_list_without_first_core.append(str(i))
    # make a list in the form of 1,2,3...
    cpu_list_for_mpstat = ','.join(cpu_list_without_first_core)
    return cpu_list_for_mpstat

def StartMpstat (Hostname, Port, Username, Password, RemoteFile):
    number_of_cpu = GetNumberOfProcessorsOnRemoteHost (Hostname, Port, Username, Password)
    cpu_list_for_mpstat = GetCpuListForMpstat (number_of_cpu)
    mpstat_grep = []
    mpstat_pids = []
    start_mpstat = "mpstat 3 -P " + str(cpu_list_for_mpstat) + " > " + str(RemoteFile) + " &"
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command('ps -A | grep mpstat')
    mpstat_grep = stdout.readlines()
    for line in mpstat_grep:
        mpstat_pids.append(line.split()[0])
    if len(mpstat_pids) > 0:
        for pid in mpstat_pids:
            stdin, stdout, stderr = s.exec_command("kill " + str(pid))
        stdin, stdout, stderr = s.exec_command(start_mpstat)
        stdin, stdout, stderr = s.exec_command('ps -A | grep mpstat')
        mpstat_current_pid = stdout.read().split()[0]
    else:
        stdin, stdout, stderr = s.exec_command(start_mpstat)
        stdin, stdout, stderr = s.exec_command('ps -A | grep mpstat')
        mpstat_current_pid = stdout.read().split()[0]
    s.close()
    return mpstat_current_pid

def StopMpstat (Hostname, Port, Username, Password):
    mpstat_grep = []
    mpstat_pids = []
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command('ps -A | grep mpstat')
    mpstat_grep = stdout.readlines()
    for line in mpstat_grep:
        mpstat_pids.append(line.split()[0])
    if len(mpstat_pids) > 0:
        for pid in mpstat_pids:
            stdin, stdout, stderr = s.exec_command("kill " + str(pid))
    else:
        print "Error in StopMpstat function var mpstat_pids < 0"
        sys.exit()
    s.close()

def GetMpstatFiles (Hostname, Port, Username, Password, LocalFile, RemoteFile):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    ftp = s.open_sftp()
    ftp.get(LocalFile, RemoteFile)
    s.close()

def NetperfUDP_test (PacketLength, RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = subprocess.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t UDP_STREAM" + " -i 3,2 " + "-l 20" + " -- " + " -m " + str(PacketLength) + " -M " + str(PacketLength), shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
    NetperfOtputs = netperf.stdout.readlines()
    return NetperfOtputs[-3].split()[-1], NetperfOtputs[-2].split()[-1]

def NetperfTCP_test (RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = subprocess.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t TCP_STREAM" + " -i 3,2 " + "-l 20", shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
    NetperfOtputs = netperf.stdout.readlines()
    return NetperfOtputs[-1].split()[-1]

def NuttcpUDP_test (Mbps, PacketLength, RemoteHostIP):
    min_Mbps_without_loss = 0
    max_Mbps_with_loss = 0
    max_speed_without_loss = 0
    i = 15
    while i != 0:
        nuttcp = subprocess.Popen("nuttcp -u -i 5 -T 10" + " -R " + str(Mbps) + "M" + " -l " + str(PacketLength) + " " + str(RemoteHostIP), shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
        nuttcpOtputs = nuttcp.stdout.readlines()
        speed_without_loss = nuttcpOtputs[-1].split()[6]
        if float(speed_without_loss) > float(max_speed_without_loss):
            max_speed_without_loss = speed_without_loss
        loss = nuttcpOtputs[-1].split()[-2]
        #print Mbps, "GenMbps"
        #print speed_without_loss, "Mbps"
        #print loss, "Loss"
        #print
        if float(loss) > 1:
            max_Mbps_with_loss = Mbps
            Mbps = (float(Mbps) + float(min_Mbps_without_loss)) / 2
        else:
            min_Mbps_without_loss = Mbps
            Mbps = (float(Mbps) + float(max_Mbps_with_loss)) / 2
        i = i - 1
    return max_speed_without_loss

def GeneralNetperfUDPTestWithMpstat (PacketLength, RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP):
    #Start Mpstat
    mpstat_current_pid_on_s1 = StartMpstat(hostname_s1, port, username, password, RemoteFileMpstatS1)
    mpstat_current_pid_on_s2 = StartMpstat(hostname_s2, port, username, password, RemoteFileMpstatS2)
    #Start Netperf test
    MaxSpeed, SpeedWithoutLoss = NetperfUDP_test (PacketLength, RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP)
    print "Netperf UDP test with Mpstat, PacketLength is ", PacketLength
    print MaxSpeed, "Throughput max 10^6bits/sec"
    print SpeedWithoutLoss, "Throughput without loss 10^6bits/sec"
    #Stop Mpstat
    StopMpstat (hostname_s1, port, username, password)
    StopMpstat (hostname_s2, port, username, password)
    #Get Mpstat files
    GetMpstatFiles(hostname_s1, port, username, password, LocalFileMpstatS1, RemoteFileMpstatS1)
    GetMpstatFiles(hostname_s2, port, username, password, LocalFileMpstatS2, RemoteFileMpstatS2)
    #Parse CPU load
    cpu_load_on_site1 = ParsingMpstatOutput(LocalFileMpstatS1, mpstat_header_regexp)
    cpu_load_on_site2 = ParsingMpstatOutput(LocalFileMpstatS2, mpstat_header_regexp)
    print cpu_load_on_site1, "CPU load on Site_1"
    print cpu_load_on_site2, "CPU load on Site_2"
    print
    time.sleep(1)

def GeneralNetperfUDPTestWithVmstat (PacketLength, RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP):
    #Start Vmstat
    vmstat_current_pid_on_s1 = StartVmstat(hostname_s1, port, username, password, RemoteFileVmstatS1)
    vmstat_current_pid_on_s2 = StartVmstat(hostname_s2, port, username, password, RemoteFileVmstatS2)
    #print vmstat_current_pid_on_s1
    #print vmstat_current_pid_on_s2
    #Start Netperf test
    MaxSpeed, SpeedWithoutLoss = NetperfUDP_test (PacketLength, RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP)
    print "Netperf UDP test with Vmstat, PacketLength is ", PacketLength
    print MaxSpeed, "Throughput max 10^6bits/sec"
    print SpeedWithoutLoss, "Throughput without loss 10^6bits/sec"
    #Stop Vmstat
    StopVmstat (hostname_s1, port, username, password)
    StopVmstat (hostname_s2, port, username, password)
    #Get Vmstat files
    GetVmstatFiles(hostname_s1, port, username, password, LocalFileVmstatS1, RemoteFileVmstatS1)
    GetVmstatFiles(hostname_s2, port, username, password, LocalFileVmstatS2, RemoteFileVmstatS2)
    #Parse CPU load
    cpu_load_on_site1 = ParsingVmstatOutput(LocalFileVmstatS1)
    cpu_load_on_site2 = ParsingVmstatOutput(LocalFileVmstatS2)
    print cpu_load_on_site1, "CPU load on Site_1"
    print cpu_load_on_site2, "CPU load on Site_2"
    print
    time.sleep(1)

print "The test is running now, please wait ..."
print
GeneralNetperfUDPTestWithMpstat (UDP1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTestWithVmstat (UDP1400, RemTrafGenMachineIP, LocTrafGenMachineIP)