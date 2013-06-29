#!/usr/bin/python

import sys, getopt
import time
import re
import warnings
import subprocess as sp
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko

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
        print bcolors.WARNING + "Error :" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
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
    print 'Local IP is ', LocTrafGenMachineIP
    print 'Remote IP is ', RemTrafGenMachineIP
    print 'Site_1 IP is ', Site_1_IP
    print 'Site_2 IP is ', Site_2_IP
    print
    return IPlist

def PingTestForOneIP (IP):
    ping = sp.Popen("ping -c 1 -w 1 " + str(IP), shell=True, executable='/bin/bash', stdout=sp.PIPE)
    PingOtputs = ping.communicate()[0]
    status = ping.returncode
    print "Status " + str(status) +" of ping IP " + str(IP)
    return status

def PingTestForIPlist (IPlist):
    number_of_reachable_ip = 0
    for IP in IPlist:
        ping = sp.Popen("ping -c 1 -w 1 " + str(IP), shell=True, executable='/bin/bash', stdout=sp.PIPE)
        PingOtputs = ping.communicate()[0]
        status = ping.returncode
        if status == 0:
            number_of_reachable_ip = number_of_reachable_ip +1
        else:
            print bcolors.WARNING + "Error :" + bcolors.ENDC + " IP " + str(IP) + " Unreachable"
            sys.exit()
    if (number_of_reachable_ip == len(IPlist)):
        print "Network test completed successfully"
        print
    else:
        sys.exit(bcolors.WARNING + "Error :" + bcolors.ENDC + " check the network settings")
        print
    return 0

def NetperfUDP_test (PacketLength, RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = sp.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t UDP_STREAM" + " -i 3,2 " + "-l 20" + " -- " + " -m " + str(PacketLength) + " -M " + str(PacketLength), shell=True, executable='/bin/bash', stdout=sp.PIPE)
    NetperfOtputs = netperf.communicate()[0].splitlines()
    status = netperf.returncode
    if status != 0:
        sys.exit(bcolors.WARNING + "Error :" + bcolors.ENDC + " netperf can't connect to the netserver " + str(RemoteHostIP) + " from " + str(LocalHostIP))
        print
    throughput_max = NetperfOtputs[-3].split()[-1]
    throughput_without_loss = NetperfOtputs[-2].split()[-1]
    return throughput_max, throughput_without_loss

def NetperfTCP_test (RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = sp.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t TCP_STREAM" + " -i 3,2 " + "-l 20", shell=True, executable='/bin/bash', stdout=sp.PIPE)
    NetperfOtputs = netperf.communicate()[0].splitlines()
    status = netperf.returncode
    if status != 0:
        sys.exit(bcolors.WARNING + "Error :" + bcolors.ENDC + " netperf can't connect to the netserver " + str(RemoteHostIP) + " from " + str(LocalHostIP))
        print
    throughput_without_loss = NetperfOtputs[-1].split()[-1]
    return throughput_without_loss

def NuttcpUDP_test (Mbps, PacketLength, RemoteHostIP, NumberOfIterations):
    min_Mbps_without_loss = 0
    max_Mbps_with_loss = 0
    max_speed_without_loss = 0
    tests_with_loss = 0
    i = NumberOfIterations
    count_of_failed_attempts = 5
    while i != 0:
        nuttcp = sp.Popen("nuttcp -u -T 10" + " -Ri " + str(Mbps) + "M" + " -l " + str(PacketLength) + " " + str(RemoteHostIP), shell=True, executable='/bin/bash', stdout=sp.PIPE)
        nuttcpOtputs = nuttcp.communicate()[0].splitlines()
        status = nuttcp.returncode
        if status != 0:
            if PingTestForOneIP(RemoteHostIP) != 0:
                sys.exit(bcolors.WARNING + "Error :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: remote host " + str(RemoteHostIP) + " Unreachable")
            else:
                if PingTestForOneIP(RemoteHostIP) == 0:
                    sys.exit(bcolors.WARNING + "Error :" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: nuttcp server on the remote host " + str(RemoteHostIP) + " not running")
        speed_without_loss = nuttcpOtputs[-1].split()[6]
        loss_of_current_test = nuttcpOtputs[-1].split()[-2]
        if float(loss_of_current_test) > 1:
            tests_with_loss = tests_with_loss + 1
            max_Mbps_with_loss = Mbps
            Mbps = (float(Mbps) + float(min_Mbps_without_loss)) / 2
        else:
            min_Mbps_without_loss = Mbps
            Mbps = (float(Mbps) + float(max_Mbps_with_loss)) / 2
        i = i - 1
        if tests_with_loss == NumberOfIterations:
            sys.exit(bcolors.WARNING + "Error :" + bcolors.ENDC + " nuttcp can't find throughput without loss")
    return speed_without_loss, loss_of_current_test

ip_list = ParseScriptArguments(sys.argv[1:])
PingTestForIPlist(ip_list)
##var1, var2 = NetperfUDP_test (1400, RemTrafGenMachineIP, LocTrafGenMachineIP)
##print var1
##print var2
##print
##var1 = NetperfTCP_test (RemTrafGenMachineIP, LocTrafGenMachineIP)
##print var1
speed, loss = NuttcpUDP_test (1000, 1400, RemTrafGenMachineIP, 5)
print speed, loss
print
speed, loss = NuttcpUDP_test (1000, 1400, RemTrafGenMachineIP, 10)
print speed, loss
print
speed, loss = NuttcpUDP_test (1000, 1400, RemTrafGenMachineIP, 15)
print speed, loss