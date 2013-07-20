#!/usr/bin/python
import IPy
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

class VmstatFilesClass:
    #Vmstat files
    LocalFileVmstatS1 = '/root/vmstat_s1'
    RemoteFileVmstatS1 = '/root/vmstat_s1'
    LocalFileVmstatS2 = '/root/vmstat_s2'
    RemoteFileVmstatS2 = '/root/vmstat_s2'

class MpstatFilesClass:
    #Mpstat files
    LocalFileMpstatS1 = '/root/mpstat_s1'
    RemoteFileMpstatS1 = '/root/mpstat_s1'
    LocalFileMpstatS2 = '/root/mpstat_s2'
    RemoteFileMpstatS2 = '/root/mpstat_s2'

class LspFilesClass:
    # LSP
    first_site_lsp_IMIT ='/root/first_site_lsp_IMIT'
    first_site_lsp_CI ='/root/first_site_lsp_CI'
    first_site_lsp_C ='/root/first_site_lsp_C'
    second_site_lsp_C_CI_IMIT = '/root/second_site_lsp_C_CI_IMIT'

class IpAdressClass:
    IpSite1 = ''
    IpSite2 = ''
    IpLocal = ''
    IpRemote = ''
    IpList = []
    def GetIpList (self):
        self.IpList.append(self.IpSite1)
        self.IpList.append(self.IpSite2)
        self.IpList.append(self.IpLocal)
        self.IpList.append(self.IpRemote)
        return self.IpList

class SshConParamsClass:
    port = 22
    username = 'root'
    password = 'russia'

class SpeedTestParamsClass:
    encrypt_alg = ''
    traf_gen = ''
    iterations = 1
    time_sync_on_sites = False
    cpu_aff_on_site1 = False
    number_cpu_for_scatter_on_site1 = 1
    number_cpu_for_encrypt_on_site1 = 1
    number_cpu_for_scatter_on_site2 = 1
    number_cpu_for_encrypt_on_site2 = 1
    cpu_aff_on_site2 = False

class NuttcpTestParamsClass:
    StartMbpsForNuttcp = 1000
    UDP1400 = 1400
    UDP512 = 512
    UDP64 = 64

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
    try:
        opts, args = getopt.getopt(argv,'hL:R:l:r:', ['help', 'ip_local=', 'ip_remote=', 'ip_site1=', 'ip_site2=', 'encr_alg=', 'traf_gen=', 'iterations=', 'time_sync_on_sites', 'cpu_aff_on_site1', 'cpu_aff_on_site2'])
    except getopt.GetoptError:
        print bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print "Usage: name_of_script.py {options} {parametrs}"
        print "options:"
        print
        print '         --ip_local            IPv4 address                    <Local traffic generator machine IP>'
        print '         --ip_remote           IPv4 address                    <Remote traffic receiver machine IP>'
        print '         --ip_site1            IPv4 address                    <First IPsec Site IP> '
        print '         --ip_site2            IPv4 address                    <Second IPsec Site IP>'
        print '         --encr_alg            {C | CI | IMIT | ALL | NOLSP}   <Encryption algorithm> '
        print '         --traf_gen            {nuttcp | netperf | ALL}        <Traffic generator>'
        print '         --iterations          {integer}                       <Test iterations>'
        print '         --time_sync_on_sites  None                            <Time syncr on IPsec Sites>'
        print '         --cpu_aff_on_site1    {{int},{int}}                   <Set CPU affinity on First IPsec Site>'
        print '         --cpu_aff_on_site2    {{int},{int}}                   <Set CPU affinity on Second IPsec Site>'
        print
        sys.exit()
    if len(opts) == 0:
        print bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print "Usage: name_of_script.py {options} {parametrs}"
        print "options:"
        print
        print '         --ip_local            IPv4 address                    <Local traffic generator machine IP>'
        print '         --ip_remote           IPv4 address                    <Remote traffic receiver machine IP>'
        print '         --ip_site1            IPv4 address                    <First IPsec Site IP> '
        print '         --ip_site2            IPv4 address                    <Second IPsec Site IP>'
        print '         --encr_alg            {C | CI | IMIT | ALL | NOLSP}   <Encryption algorithm> '
        print '         --traf_gen            {nuttcp | netperf | ALL}        <Traffic generator>'
        print '         --iterations          {integer}                       <Test iterations>'
        print '         --time_sync_on_sites  None                            <Time syncr on IPsec Sites>'
        print '         --cpu_aff_on_site1    {{int},{int}}                   <Set CPU affinity on First IPsec Site>'
        print '         --cpu_aff_on_site2    {{int},{int}}                   <Set CPU affinity on Second IPsec Site>'
        print
        sys.exit()
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print "Usage: name_of_script.py {options} {parametrs}"
            print "options:"
            print
            print '         --ip_local            IPv4 address                    <Local traffic generator machine IP>'
            print '         --ip_remote           IPv4 address                    <Remote traffic receiver machine IP>'
            print '         --ip_site1            IPv4 address                    <First IPsec Site IP> '
            print '         --ip_site2            IPv4 address                    <Second IPsec Site IP>'
            print '         --encr_alg            {C | CI | IMIT | ALL | NOLSP}   <Encryption algorithm> '
            print '         --traf_gen            {nuttcp | netperf | ALL}        <Traffic generator>'
            print '         --iterations          {integer}                       <Test iterations>'
            print '         --time_sync_on_sites  None                            <Time syncr on IPsec Sites>'
            print '         --cpu_aff_on_site1    {{int},{int}}                   <Set CPU affinity on First IPsec Site>'
            print '         --cpu_aff_on_site2    {{int},{int}}                   <Set CPU affinity on Second IPsec Site>'
            print
            sys.exit()
        elif opt in ('--time_sync_on_sites'):
            SpeedTestParams.time_sync_on_sites = True
        elif opt in ('--cpu_aff_on_site1'):
            SpeedTestParams.cpu_aff_on_site1 = True
            SpeedTestParams.number_cpu_for_scatter_on_site1 = arg.split()[0]
            SpeedTestParams.number_cpu_for_encrypt_on_site1 = arg.split()[1]
        elif opt in ('--cpu_aff_on_site2'):
            SpeedTestParams.cpu_aff_on_site2 = True
            SpeedTestParams.number_cpu_for_scatter_on_site2 = arg.split()[0]
            SpeedTestParams.number_cpu_for_encrypt_on_site2 = arg.split()[1]
        elif opt in ('--ip_local'):
            try:
                IPy.IP(arg)
            except:
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameter of \"--ip_local\" option, must be IPv4 address")
            else:
                IpAdress.IpLocal = arg
        elif opt in ('--ip_remote'):
            try:
                IPy.IP(arg)
            except:
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameter of \"--ip_remote\" option, must be IPv4 address")
            else:
                IpAdress.IpRemote = arg
        elif opt in ('--ip_site2'):
            try:
                IPy.IP(arg)
            except:
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameter of \"--ip_site2\" option, must be IPv4 address")
            else:
                IpAdress.IpSite2 = arg
        elif opt in ('--ip_site1'):
            try:
                IPy.IP(arg)
            except:
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameter of \"--ip_site1\" option, must be IPv4 address")
            else:
                IpAdress.IpSite1 = arg
        elif opt in ('--encr_alg'):
            if arg not in ('C', 'CI', 'IMIT', 'ALL', 'NOLSP'):
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameter of \"--encr_alg\" option, must be [C|CI|IMIT|ALL|NOLSP]")
            SpeedTestParams.encrypt_alg = arg
        elif opt in ('--traf_gen'):
            if arg not in ('nuttcp','netperf','ALL'):
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameter of \"--traf_gen\" option, must be [nuttcp|netperf|ALL]")
            else:
                SpeedTestParams.traf_gen = arg
        elif opt in ('--iterations'):
            if arg.isdigit() == False:
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameter of \"---number\" option, must be integer")
            else:
                SpeedTestParams.iterations = int(arg)
    if (IpAdress.IpLocal == '') or (IpAdress.IpRemote == '') or (IpAdress.IpSite2 == '') or (IpAdress.IpSite1 == '') or (SpeedTestParams.encrypt_alg == '') or (SpeedTestParams.iterations == ''):
        print bcolors.FAIL + "Error:" + bcolors.ENDC + " check parameters of script, please see the following syntax:"
        print
        print "Usage: name_of_script.py {options} {parametrs}"
        print "options:"
        print
        print '         --ip_local            IPv4 address                    <Local traffic generator machine IP>'
        print '         --ip_remote           IPv4 address                    <Remote traffic receiver machine IP>'
        print '         --ip_site1            IPv4 address                    <First IPsec Site IP> '
        print '         --ip_site2            IPv4 address                    <Second IPsec Site IP>'
        print '         --encr_alg            {C | CI | IMIT | ALL | NOLSP}   <Encryption algorithm> '
        print '         --traf_gen            {nuttcp | netperf | ALL}        <Traffic generator>'
        print '         --iterations          {integer}                       <Test iterations>'
        print '         --time_sync_on_sites  None                            <Time syncr on IPsec Sites>'
        print '         --cpu_aff_on_site1    {{int},{int}}                   <Set CPU affinity on First IPsec Site>'
        print '         --cpu_aff_on_site2    {{int},{int}}                   <Set CPU affinity on Second IPsec Site>'
        print
        sys.exit()
    print 'Local  IP:                       ', IpAdress.IpLocal
    print 'Remote IP:                       ', IpAdress.IpRemote
    print 'Site 1 IP:                       ', IpAdress.IpSite1
    print 'Site 2 IP:                       ', IpAdress.IpSite2
    print 'Encryption algorithm:            ', SpeedTestParams.encrypt_alg
    print 'Traffic generator:               ', SpeedTestParams.traf_gen
    print 'Time sync on sites:              ', SpeedTestParams.time_sync_on_sites
    print 'CPU aff. on Site 1:              ', SpeedTestParams.cpu_aff_on_site1
    print '     Num. for scatter on Site 1: ', SpeedTestParams.number_cpu_for_scatter_on_site1
    print '     Num. for encrypt on Site 1: ', SpeedTestParams.number_cpu_for_encrypt_on_site1
    print 'CPU aff. on Site 2:              ', SpeedTestParams.cpu_aff_on_site2
    print '     Num. for scatter on Site 2: ', SpeedTestParams.number_cpu_for_scatter_on_site2
    print '     Num. for encrypt on Site 2: ', SpeedTestParams.number_cpu_for_encrypt_on_site2
    print 'Number of iterations:            ', SpeedTestParams.iterations
    print

def PingTest (IPlist):
    number_of_reachable_ip = 0
    if len(IPlist) == 0:
        sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " PingTest(IPlist), IPlist is Null")
    if len(IPlist) == 1:
        ping = sp.Popen("ping -c 1 -w 1 " + str(IPlist[0]), shell=True, executable='/bin/bash', stdout=sp.PIPE)
        PingOtputs = ping.communicate()[0]
        status = ping.returncode
        return status # return 0 if IP reachable
    if len(IPlist) > 1:
        for IP in IPlist:
            ping = sp.Popen("ping -c 1 -w 1 " + str(IP), shell=True, executable='/bin/bash', stdout=sp.PIPE)
            PingOtputs = ping.communicate()[0]
            status = ping.returncode
            if status == 0:
                number_of_reachable_ip = number_of_reachable_ip +1
            else:
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " IP " + str(IP) + " Unreachable, check the network settings")
    return 0
IpAdress = IpAdressClass()
SpeedTestParams = SpeedTestParamsClass ()
ParseScriptArguments(sys.argv[1:])
print PingTest(IpAdress.GetIpList())