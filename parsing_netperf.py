#!/usr/bin/python
import time
import sys
import warnings
import subprocess
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko

port = 22
hostname_s1 = '192.168.7.2'
hostname_s2 = '192.168.8.2'
LocTrafGenMachineIP = '192.168.7.1'
RemTrafGenMachineIP = '192.168.8.1'
username = 'root'
password = 'russia'
LocalFileVmstatS1 = '/root/vmstat_s1'
RemoteFileVmstatS1 = '/root/vmstat_s1'
LocalFileVmstatS2 = '/root/vmstat_s2'
RemoteFileVmstatS2 = '/root/vmstat_s2'
StartMbpsForNuttcp = 1000
UDP1400 = 1400
UDP512 = 512
UDP64 = 64

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
    s.close()

def NetperfUDP_test (PacketLength, RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = subprocess.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t UDP_STREAM" + " -i 5,5 " + "-l 20" + " -- " + " -m " + str(PacketLength) + " -M " + str(PacketLength), shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
    NetperfOtputs = netperf.stdout.readlines()
    return NetperfOtputs[-3].split()[-1], NetperfOtputs[-2].split()[-1]

def NetperfTCP_test (RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = subprocess.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t TCP_STREAM" + " -i 5,5 " + "-l 20", shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
    NetperfOtputs = netperf.stdout.readlines()
    return NetperfOtputs[-1].split()[-1]

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
    avg = sum(cpu_load)/float(len(cpu_load))

    #create new list where items > approximate average
    for i in cpu_load:
        if i > avg:
            true_cpu_load.append(i)
    return sum(true_cpu_load)/float(len(true_cpu_load))

def RestartVpnDaemon (Hostname, Port, Username, Password):
    restart_daemon = "/etc/init.d/vpndrv stop; /etc/init.d/vpndrv start; /etc/init.d/vpngate start"
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(Hostname, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command(restart_daemon)
    daemon_out = stdout.readlines()
    #for line in daemon_out:
        #print line.strip()

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

def GeneralNetperfUDPTest (PacketLength, RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP):
    #Start Vmstat
    vmstat_current_pid_on_s1 = StartVmstat(hostname_s1, port, username, password, RemoteFileVmstatS1)
    vmstat_current_pid_on_s2 = StartVmstat(hostname_s2, port, username, password, RemoteFileVmstatS2)
    #print vmstat_current_pid_on_s1
    #print vmstat_current_pid_on_s2
    #Start Netperf test
    MaxSpeed, SpeedWithoutLoss = NetperfUDP_test (PacketLength, RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP)
    print "Test Netperf UDP, PacketLength is ", PacketLength
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

def GeneralNetperfTCPTest (RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP):
    #Start Vmstat
    vmstat_current_pid_on_s1 = StartVmstat(hostname_s1, port, username, password, RemoteFileVmstatS1)
    vmstat_current_pid_on_s2 = StartVmstat(hostname_s2, port, username, password, RemoteFileVmstatS2)
    #print vmstat_current_pid_on_s1
    #print vmstat_current_pid_on_s2
    #Start Netperf test
    Speed = NetperfTCP_test (RemoteTrafficGeneratorMachineIP, LocalTrafficGeneratorMachineIP)
    print "Test Netperf TCP"
    print Speed, "Throughput 10^6bits/sec"
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
def GeneralNuttcpUDPTest (StartMbps, PacketLength, RemoteTrafficGeneratorMachineIP):
    #Start Vmstat
    vmstat_current_pid_on_s1 = StartVmstat(hostname_s1, port, username, password, RemoteFileVmstatS1)
    vmstat_current_pid_on_s2 = StartVmstat(hostname_s2, port, username, password, RemoteFileVmstatS2)
    Speed = NuttcpUDP_test (StartMbps, PacketLength, RemoteTrafficGeneratorMachineIP)
    print Speed, "Mbps, PacketLength is", PacketLength
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
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP1400, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP512, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP64, RemTrafGenMachineIP)
GeneralNetperfUDPTest (UDP1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP512, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP64, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfTCPTest (RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP1400, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP512, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP64, RemTrafGenMachineIP)
GeneralNetperfUDPTest (UDP1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP512, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP64, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfTCPTest (RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP1400, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP512, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP64, RemTrafGenMachineIP)
GeneralNetperfUDPTest (UDP1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP512, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP64, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfTCPTest (RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP1400, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP512, RemTrafGenMachineIP)
GeneralNuttcpUDPTest (StartMbpsForNuttcp, UDP64, RemTrafGenMachineIP)
GeneralNetperfUDPTest (UDP1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP512, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfUDPTest (UDP64, RemTrafGenMachineIP, LocTrafGenMachineIP)
GeneralNetperfTCPTest (RemTrafGenMachineIP, LocTrafGenMachineIP)