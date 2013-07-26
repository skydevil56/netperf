#!/usr/bin/python
import os
import hashlib
import time
import sys, getopt
import re
import warnings
import optparse
import subprocess as sp
import locale
locale.setlocale(locale.LC_NUMERIC, "")

def format_num(num):
    """Format a number according to given places.
    Adds commas, etc. Will truncate floats into ints!"""

    try:
        inum = int(num)
        return locale.format("%.*f", (0, inum), True)

    except (ValueError, TypeError):
        return str(num)

def get_max_width(table, index):
    """Get the maximum width of the given column index"""

    return max([len(format_num(row[index])) for row in table])

def pprint_table(out, table):
    """Prints out a table of data, padded for alignment
    @param out: Output stream (file-like object)
    @param table: The table to print. A list of lists.
    Each row must have the same number of columns. """

    col_paddings = []

    for i in range(len(table[0])):
        col_paddings.append(get_max_width(table, i))

    for row in table:
        # left col
        print >> out, row[0].ljust(col_paddings[0] + 1),
        # rest of the cols
        for i in range(1, len(row)):
            col = format_num(row[i]).rjust(col_paddings[i] + 2)
            print >> out, col,
        print >> out

class SummTables:
    table_with_cpu_load = [["", "Mbps", "CPU load on Site 1", "CPU load on Site 2"],
        ["UDP1400", 0.0, 0.0, 0.0],
        ["UDP1000", 0.0, 0.0, 0.0],
        ["UDP512", 0.0, 0.0, 0.0],
        ["UDP64", 0.0, 0.0, 0.0],
        ["TCP", 0.0, 0.0, 0.0],
        ["IMIX", 0.0, 0.0, 0.0]]

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

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        import paramiko
    except ImportError:
        sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " python-paramiko not install. Python module for make ssh v2 connections with Python")
try:
    import IPy
except ImportError:
    sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " python-ipy not install. Python module for handling IPv4 and IPv6 addresses and networks")

vpndrvr_cpu_distribution_regexp = re.compile('options[\s]vpndrvr[\s]cpu_distribution="\*\:([\d]{1,2})/([\d]{1,2})"')
mpstat_header_regexp = re.compile('[\d]{2}:[\d]{2}:[\d]{2}[\s]{0,}CPU[\s]{0,}%usr[\s]{1,}%nice[\s]{1,}%sys[\s]{1,}%iowait[\s]{1,}%irq[\s]{1,}%soft[\s]{1,}%steal[\s]{1,}%guest[\s]{1,}%idle|^[\s]{1,}|Linux.{0,}[\(][\s]{0,}[\d]{1,}[\s]{1,}CPU[\s]{0,}[\)][\s]{0,}')

class VpndrvrFilesClass:
    #Vpndrvr files
    LocalVpndrvrFile = '/root/vpndrvr.conf'
    RemoteVpndrvrFile = '/etc/modprobe.d/vpndrvr.conf'

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

class NuttcpTestParamsClass:
    IterationsForRepeatTest = 10
    StartMbpsForNuttcp = 1000
    UDP1400 = 1400
    UDP1000 = 1000
    UDP512 = 512
    UDP64 = 64

class NetperfTestParamsClass:
    TimeForImixTest = 60
    UDP1400 = 1400
    UDP1000 = 1000
    UDP512 = 512
    UDP64 = 64

class SpeedTestParamsClass:
    encrypt_alg = ''
    traf_gen = ''
    iterations = 1
    time_sync_on_sites = False
    cpu_aff_on_site1 = True
    cpu_aff_on_site2 = True
    number_cpu_for_scatter_on_site1 = 1
    number_cpu_for_encrypt_on_site1 = 1
    number_cpu_for_scatter_on_site2 = 1
    number_cpu_for_encrypt_on_site2 = 1
    cpu_stat = False
    verbose = False
    def SetNumberCpuForScatterOnSite1 (self, num):
        self.cpu_aff_on_site1 = True
        self.number_cpu_for_scatter_on_site1 = num
    def SetNumberCpuForScatterOnSite2 (self, num):
        self.cpu_aff_on_site2 = True
        self.number_cpu_for_scatter_on_site2 = num
    def SetNumberCpuForEncryptOnSite1 (self, num):
        self.cpu_aff_on_site1 = True
        self.number_cpu_for_encrypt_on_site1 = num
    def SetNumberCpuForEncryptOnSite2 (self, num):
        self.cpu_aff_on_site2 = True
        self.number_cpu_for_encrypt_on_site2 = num

desc = "Speed test for S-Terra Gate"
parser = optparse.OptionParser(description=desc)
parser.add_option('--ip_local', help='Local traffic generator machine IP', dest='ip_local', action='store', metavar='{IPv4 address}', nargs=1)
parser.add_option('--ip_remote', help='Remote traffic receiver machine IP', dest='ip_remote', action='store', metavar='{IPv4 address}', nargs=1)
parser.add_option('--ip_site1', help='First IPsec Site IP', dest='ip_site1', action='store', metavar='{IPv4 address}', nargs=1)
parser.add_option('--ip_site2', help='Second IPsec Site IP', dest='ip_site2', action='store', metavar='{IPv4 address}', nargs=1)
parser.add_option('--encr_alg', help='Encryption algorithm. A default value [%default]', dest='encr_alg', action='store', metavar='{C | CI | IMIT | ALL | NOLSP}', default='NOLSP')
parser.add_option('--traf_gen', help='Traffic generator. A default value [%default]', dest='traf_gen', action='store', metavar='{nuttcp | netperf | ALL}', default='netperf')
parser.add_option('--iterations', help='Test iterations. A default value [%default]', dest='iterations', action='store', metavar='{integer}', type='int', default=1)
parser.add_option('--time_sync_on_sites', help='Time syncr on two IPsec Sites. A default value [%default]', dest='time_sync_on_sites', default=False, action='store_true')
parser.add_option('--cpu_aff_on_site1', help='Set CPU affinity on first IPsec Site. A default value [%default]', dest='cpu_aff_on_site1', default=False, action='store', metavar='{{num cores for scatter} {num cores for encrypt}}', nargs=2, type='int')
parser.add_option('--cpu_aff_on_site2', help='Set CPU affinity on second IPsec Site. A default value [%default]', dest='cpu_aff_on_site2', default=False, action='store', metavar='{{int},{int}}', nargs=2, type='int')
parser.add_option('--cpu_stat', help='Show CPU load on IPsec Sites. A default value [%default]', dest='cpu_stat', default=False, action='store_true')
parser.add_option('--verbose', help='More information during the test. A default value [%default]', dest='verbose', default=False, action='store_true')
(opts, args) = parser.parse_args()

def CheckStartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName):
    # if return status is 0 - remote daemon is now running
    # if return status is 1 - remote daemon is not running

    if DaemonName == 'vpngate': # special for SterrGate =)
        DaemonName = 'vpnsvc'
    if DaemonName == 'vpndrv':
        DaemonName = 'vpndrvr'
    check_daemon_is_starting = "ps -A | grep " + str(DaemonName)
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        s.connect(RemoteHostIP, Port, Username, Password)
    except:
        sys.exit(bcolors.FAIL + "[Error in CheckStartRemoteDaemon]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
    else:
        stdin, stdout, stderr = s.exec_command(check_daemon_is_starting)
        status = stdout.channel.recv_exit_status()
        if (status != 0) and (status != 1):
            s.close()
            sys.exit(bcolors.FAIL + "[Error in CheckStartRemoteDaemon]:" + bcolors.ENDC + "  Can't check start remote daemon: " + str(DaemonName) + " on host: " + \
            str (RemoteHostIP) + " .Was obtained unknown status: " + str(status))
        else:
            if SpeedTestParams.verbose:
                if status == 0:
                    print bcolors.OKGREEN + "[Info in CheckStartRemoteDaemon]: " + bcolors.ENDC + " Daemon: " + str(DaemonName) + " is running now" + " on remote host: " + str (RemoteHostIP)
                else:
                    print bcolors.OKGREEN + "[Info in CheckStartRemoteDaemon]: " + bcolors.ENDC + " Daemon: " + str(DaemonName) + " not running now" + " on remote host: " + str (RemoteHostIP)
    s.close()
    return status

def StopRemoteDaemonThroughInitd (RemoteHostIP, Port, Username, Password, DaemonName):
    # if return status is 0 - remote daemon is stop
    # if return status is 1 - remote daemon already not running

    # check what remote daemon is start
    if CheckStartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 0:
        stop_remote_daemon = "/etc/init.d/" + str(DaemonName) + " stop"
        # print bcolors.OKGREEN + "Info: " + bcolors.ENDC +
        paramiko.util.log_to_file('paramiko.log')
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "[Error in StopRemoteDaemonThroughInitd]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            stdin, stdout, stderr = s.exec_command(stop_remote_daemon)
            status = stdout.channel.recv_exit_status()
            if status != 0:
                s.close()
                sys.exit(bcolors.FAIL + "[Error in StopRemoteDaemonThroughInitd]: " + bcolors.ENDC + " Can't stop remote daemon: " + str(DaemonName) + " on remote host: " + str(RemoteHostIP))
            else:
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in StopRemoteDaemonThroughInitd]: " + bcolors.ENDC + " Daemon: " + str(DaemonName) + " was stopped" + " on remote host: " + str (RemoteHostIP)
            s.close()
            return 0
    else:
        return 1

def StartRemoteDaemonThroughInitd (RemoteHostIP, Port, Username, Password, DaemonName):
    # if return status is 0 - remote daemon was start
    # if return status is 1 - remote daemon already start

    # check what remote daemon already not start
    if CheckStartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 1:
        start_remote_daemon = "/etc/init.d/" + str(DaemonName) + " start"
        # print bcolors.OKGREEN + "Info: " + bcolors.ENDC +
        paramiko.util.log_to_file('paramiko.log')
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "[Error in StartRemoteDaemonThroughInitd]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            stdin, stdout, stderr = s.exec_command(start_remote_daemon)
            status = stdout.channel.recv_exit_status()
            if status != 0:
                s.close()
                sys.exit(bcolors.FAIL + "[Error in StartRemoteDaemonThroughInitd]: " + bcolors.ENDC + " Can't start remote daemon: " + str(DaemonName) + " on remote host: " + str(RemoteHostIP))
            else:
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in StartRemoteDaemonThroughInitd]: " + bcolors.ENDC + " Daemon: " + str(DaemonName) + " was starter" + " on remote host: " + str (RemoteHostIP)
            s.close()
            return 0
    else:
        return 1

def RestartRemoteSterraGate (RemoteHostIP, Port, Username, Password):
    restart_remote_sterra = "/etc/init.d/vpngate stop && /etc/init.d/vpndrv stop && /etc/init.d/vpndrv start && /etc/init.d/vpngate start"
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        s.connect(RemoteHostIP, Port, Username, Password)
    except:
        sys.exit(bcolors.FAIL + "[Error in RestartRemoteSterraGate]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
    else:
        stdin, stdout, stderr = s.exec_command(restart_remote_sterra)
        status = stdout.channel.recv_exit_status()
        if status != 0:
            s.close()
            sys.exit(bcolors.FAIL + "[Error in RestartRemoteSterraGate]: " + bcolors.ENDC + " Can't restart remote S-Terra Gate on host: " + str(RemoteHostIP))
        else:
            pass
            if SpeedTestParams.verbose:
                print bcolors.OKGREEN + "[Info in RestartRemoteSterraGate]: " + bcolors.ENDC + " S-Terra Gate on host: " + str (RemoteHostIP) + " successful restart"
        s.close()

def CheckStartrLocalDaemon (DaemonName):
    # if return status is 0 - local daemon is now running
    # if return status is 1 - local daemon is not running
    daemon_is_start_out = []
    daemon_is_start = sp.Popen("ps -A | grep " + str(DaemonName), shell=True, executable='/bin/bash', stdout=sp.PIPE)
    daemon_is_start_out = daemon_is_start.communicate()[0].splitlines()
    status = daemon_is_start.returncode
    if (status != 0) and (status != 1):
        sys.exit(bcolors.FAIL + "[Error in CheckStartrLocalDaemon]: " + bcolors.ENDC + " Can't check start local daemon: " + str(DaemonName) + ". Was obtained unknown status: " + str(status))
    return status

def StartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName, Parametrs = '', OutputFile = ''):
    # if return status is 0 - remote daemon was successfully start
    # if return status is 1 - remote daemon was't start

    # check what remote daemon is't stat
    if CheckStartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 0:
        return 1
    else:
        if OutputFile == '':
            start_remote_daemon = str(DaemonName) + " " + str(Parametrs)
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                s.connect(RemoteHostIP, Port, Username, Password)
            except:
                sys.exit(bcolors.FAIL + "[Error in StartRemoteDaemon]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
            else:
                stdin, stdout, stderr = s.exec_command(start_remote_daemon)
                status = stdout.channel.recv_exit_status()
                if (status != 0) and (status != 1):
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in StartRemoteDaemon]: " + bcolors.ENDC + " Can't start remote daemon: " + str(DaemonName) + " On host: " + \
                    str (RemoteHostIP) + " . Was obtained unknown status: " + str(status))
                s.close()
                return status
        else:
            if OutputFile != '':
                start_remote_daemon = str(DaemonName) + " " + str(Parametrs) + " > " + str(OutputFile) + " &"
                paramiko.util.log_to_file('paramiko.log')
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    s.connect(RemoteHostIP, Port, Username, Password)
                except:
                    sys.exit(bcolors.FAIL + "[Error in StartRemoteDaemon]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
                else:
                    stdin, stdout, stderr = s.exec_command(start_remote_daemon)
                    status = stdout.channel.recv_exit_status()
                    if (status != 0) and (status != 1):
                        s.close()
                        sys.exit(bcolors.FAIL + "[Error in StartRemoteDaemon]: " + bcolors.ENDC + " Can't start remote daemon: " + str(DaemonName) + " On host: " + \
                        str (RemoteHostIP) + " . Was obtained unknown status: " + str(status))
                    s.close()
                    return status

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
                sys.exit(bcolors.FAIL + "[Error in StartLocalDaemon]: " + bcolors.ENDC + " Can't start local daemon: " + str(DaemonName) + " . Was obtained unknown status: " + str(status))
            return status
        else:
            if OutputFile != '':
                daemon_start_out = []
                start_local_daemon = str(DaemonName) + " " + str(Parametrs) + " > " + str(OutputFile) + " &"
                daemon_is_start = sp.Popen(start_local_daemon, shell=True, executable='/bin/bash', stdout=sp.PIPE)
                daemon_start_out = daemon_is_start.communicate()[0].splitlines()
                status = daemon_is_start.returncode
                if (status != 0) and (status != 1):
                    sys.exit(bcolors.FAIL + "[Error in StartLocalDaemon]: " + bcolors.ENDC + " Can't start local daemon: " + str(DaemonName) + " . Was obtained unknown status: " + str(status))
                return status
    return

def StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams (RemoteHostIP, Port, Username, Password, DaemonName, Parametrs = '', OutputFile = ''):
    # if return status is 0 - remote daemon was successfully start
    # if return status is 1 - remote daemon was't start
    if OutputFile == '':
        start_remote_daemon = str(DaemonName) + " " + str(Parametrs)
        paramiko.util.log_to_file('paramiko.log')
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "[Error in StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            stdin, stdout, stderr = s.exec_command(start_remote_daemon)
            status = stdout.channel.recv_exit_status()
            if (status != 0) and (status != 1):
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams]: " + bcolors.ENDC + " Can't start another instance of remote daemon: " + str(DaemonName) + " On host: " + \
                    str (RemoteHostIP) + " . Was obtained unknown status: " + str(status))
            s.close()
            return status
    else:
        if OutputFile != '':
            start_remote_daemon = str(DaemonName) + " " + str(Parametrs) + " > " + str(OutputFile) + " &"
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                s.connect(RemoteHostIP, Port, Username, Password)
            except:
                sys.exit(bcolors.FAIL + "[Error in StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
            else:
                stdin, stdout, stderr = s.exec_command(start_remote_daemon)
                status = stdout.channel.recv_exit_status()
                if (status != 0) and (status != 1):
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams]: " + bcolors.ENDC + " Can't start another instance of remote daemon: " + str(DaemonName) + " On host: " + \
                    str (RemoteHostIP) + " . Was obtained unknown status: " + str(status))
                s.close()
                return status

def StopRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName):
    # if return status is 0 - remote daemon is stop
    # if return status is 1 - remote daemon already not running

    # check what remote daemon is start
    if CheckStartRemoteDaemon (RemoteHostIP, Port, Username, Password, DaemonName) == 0:
        stop_remote_daemon = "killall " + str(DaemonName)
        paramiko.util.log_to_file('paramiko.log')
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "[Error in StopRemoteDaemon]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            stdin, stdout, stderr = s.exec_command(stop_remote_daemon)
            status = stdout.channel.recv_exit_status()
            if status != 0:
                s.close()
                sys.exit(bcolors.FAIL + "[Error in StopRemoteDaemon]: " + bcolors.ENDC + " Can't stop remote daemon: " + str(DaemonName) + " on remote host: " + str(RemoteHostIP))
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
            sys.exit(bcolors.FAIL + "[Error in StopLocalDaemon]: " + bcolors.ENDC + " Can't stop local daemon: " + str(DaemonName))
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

def SetTimeOnRemoteHostAsLocalHost (RemoteHostIP, Port, Username, Password):
    get_time_on_local_host = "date +%m%d%H%M%G"
    get_time = sp.Popen(get_time_on_local_host, shell=True, executable='/bin/bash', stdout=sp.PIPE)
    time = get_time.communicate()[0].splitlines()[0]
    status_of_get_time = get_time.returncode
    if status_of_get_time == 0:
        if SpeedTestParams.verbose:
            print bcolors.OKGREEN + "[Info in SetTimeOnRemoteHostAsLocalHost]: " + bcolors.ENDC + " Time on local host: " + str (time)
        set_time = "date " + str(time)
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "[Error in SetTimeOnRemoteHostAsLocalHost]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            stdin, stdout, stderr = s.exec_command(set_time)
            status_of_set_time = stdout.channel.recv_exit_status()
            if status_of_set_time == 0:
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in SetTimeOnRemoteHostAsLocalHost]: " + bcolors.ENDC + " Time on remote host was set: " + str (time)
            else:
                sys.exit(bcolors.FAIL + "[Error in SetTimeOnRemoteHostAsLocalHost]: " + bcolors.ENDC + " Can't set time on remote host: " + str(RemoteHostIP))
        finally:
            s.close()
    else:
        sys.exit(bcolors.FAIL + "[Error in SetTimeOnRemoteHostAsLocalHost]: " + bcolors.ENDC + " Can't get time with local host")

def GetTimeFromRemoteHost (RemoteHostIP, Port, Username, Password):
    get_time = "date"
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        s.connect(RemoteHostIP, Port, Username, Password)
    except:
        sys.exit(bcolors.FAIL + "[Error in GetTimeFromRemoteHost]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
    else:
        stdin, stdout, stderr = s.exec_command(get_time)
        status_of_get_time = stdout.channel.recv_exit_status()
        if status_of_get_time == 0:
            time = stdout.readlines()[0]
            if SpeedTestParams.verbose:
                print bcolors.OKGREEN + "[Info in GetTimeFromRemoteHost]: " + bcolors.ENDC + " Time: " + str(time) + " on remote host: " + str(RemoteHostIP)
            return time
        else:
            sys.exit(bcolors.FAIL + "[Error in GetTimeFromRemoteHost]: " + bcolors.ENDC + " Can't get time from remote host: " + str(RemoteHostIP))
    finally:
        s.close()

def ParsingParametrsOfScript ():
    # check local traffic generator machine IP
    try:
        IPy.IP(opts.ip_local)
    except:
        print bcolors.FAIL + "[Error in ParsingParametrsOfScript]: " + bcolors.ENDC + " Wrong format of IPv4 Address: " + str(opts.ip_local)
        parser.print_help()
        sys.exit()
    else:
        IpAdress.IpLocal = opts.ip_local
    # check remote traffic receiver machine IP
    try:
        IPy.IP(opts.ip_remote)
    except:
        print bcolors.FAIL + "[Error in ParsingParametrsOfScript]:" + bcolors.ENDC + " Wrong format of IPv4 Address: " + str(opts.ip_remote)
        parser.print_help()
        sys.exit()
    else:
        IpAdress.IpRemote = opts.ip_remote
    # check first IPsec Site IP
    try:
        IPy.IP(opts.ip_site1)
    except:
        print bcolors.FAIL + "[Error in ParsingParametrsOfScript]: " + bcolors.ENDC + " Wrong format of IPv4 Address: " + str(opts.ip_site1)
        parser.print_help()
        sys.exit()
    else:
        IpAdress.IpSite1 = opts.ip_site1
    # check second IPsec Site IP
    try:
        IPy.IP(opts.ip_site2)
    except:
        print bcolors.FAIL + "[Error in ParsingParametrsOfScript]: " + bcolors.ENDC + " Wrong format of IPv4 Address: " + str(opts.ip_site2)
        parser.print_help()
        sys.exit()
    else:
        IpAdress.IpSite2 = opts.ip_site2
    # check encryption algorithm
    if opts.encr_alg == 'NOLSP':
        SpeedTestParams.encrypt_alg = opts.encr_alg
    else:
        if opts.encr_alg in ('C', 'CI', 'IMIT', 'ALL'):
            SpeedTestParams.encrypt_alg = opts.encr_alg
        else:
            print bcolors.FAIL + "[Error in ParsingParametrsOfScript]: " + bcolors.ENDC + " Unknown encryption algorithm: " + str(opts.encr_alg)
            parser.print_help()
            sys.exit()
    # check traffic generator
    if opts.traf_gen == 'netperf':
        SpeedTestParams.traf_gen = opts.traf_gen
    else:
        if opts.traf_gen in ('nuttcp', 'ALL'):
            SpeedTestParams.traf_gen = opts.traf_gen
        else:
            print bcolors.FAIL + "[Error in ParsingParametrsOfScript]: " + bcolors.ENDC + " Unknown traffic generator: " + str(opts.traf_gen)
            parser.print_help()
            sys.exit()
    # check time syncr
    if not opts.time_sync_on_sites:
        SpeedTestParams.time_sync_on_sites = opts.time_sync_on_sites
    else:
        SpeedTestParams.time_sync_on_sites = opts.time_sync_on_sites
    # check CPU stat
    if not opts.cpu_stat:
        SpeedTestParams.cpu_stat = opts.cpu_stat
    else:
        SpeedTestParams.cpu_stat = opts.cpu_stat
    # check verbose
    if not opts.verbose:
        SpeedTestParams.verbose = False
    else:
        SpeedTestParams.verbose = opts.verbose
    # check CPU affinity on first IPsec Site
    if not opts.cpu_aff_on_site1:
        SpeedTestParams.cpu_aff_on_site1 = False
    else:
        SpeedTestParams.SetNumberCpuForScatterOnSite1(opts.cpu_aff_on_site1[0])
        SpeedTestParams.SetNumberCpuForEncryptOnSite1(opts.cpu_aff_on_site1[1])
    # check CPU affinity on second IPsec Site
    if not opts.cpu_aff_on_site2:
        SpeedTestParams.cpu_aff_on_site2 = False
    else:
        SpeedTestParams.SetNumberCpuForScatterOnSite2(opts.cpu_aff_on_site2[0])
        SpeedTestParams.SetNumberCpuForEncryptOnSite2(opts.cpu_aff_on_site2[1])
    # check test iterations
    if not opts.iterations:
        SpeedTestParams.iterations = 1
    else:
        SpeedTestParams.iterations = opts.iterations

def PrintSummaryOfTest ():
    print 'Local  IP:                       ', IpAdress.IpLocal
    print 'Remote IP:                       ', IpAdress.IpRemote
    print 'Site 1 IP:                       ', IpAdress.IpSite1
    print 'Site 2 IP:                       ', IpAdress.IpSite2
    print 'Encryption algorithm:            ', SpeedTestParams.encrypt_alg
    print 'Traffic generator:               ', SpeedTestParams.traf_gen
    print 'Time sync on sites:              ', SpeedTestParams.time_sync_on_sites
    if SpeedTestParams.time_sync_on_sites:
        print "     Current time on Site 1: ", (GetTimeFromRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password)).strip()
        print "     Current time on Site 2: ", (GetTimeFromRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password)).strip()
    print 'CPU aff. on Site 1:              ', SpeedTestParams.cpu_aff_on_site1
    if SpeedTestParams.cpu_aff_on_site1 == True:
        print '     Num. Cores for scatter: ', SpeedTestParams.number_cpu_for_scatter_on_site1
        print '     Num. Cores for encrypt: ', SpeedTestParams.number_cpu_for_encrypt_on_site1
    print 'CPU aff. on Site 2:              ', SpeedTestParams.cpu_aff_on_site2
    if SpeedTestParams.cpu_aff_on_site2 == True:
        print '     Num. Cores for scatter: ', SpeedTestParams.number_cpu_for_scatter_on_site2
        print '     Num. Cores for encrypt: ', SpeedTestParams.number_cpu_for_encrypt_on_site2
    print 'Show CPU load on IPsec Sites:    ', SpeedTestParams.cpu_stat
    print 'Number of iterations:            ', SpeedTestParams.iterations
    print 'Verbose:                         ', SpeedTestParams.verbose

def PingTest (IPlist):
    number_of_reachable_ip = 0
    if len(IPlist) == 0:
        sys.exit(bcolors.FAIL + "[Error in PingTest]: " + bcolors.ENDC + " PingTest(IPlist), IPlist is Null")
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
                sys.exit(bcolors.FAIL + "[Error in PingTest]: " + bcolors.ENDC + " IP " + str(IP) + " Unreachable, check the network settings")
    return 0

def CheckInstallProgramOnRemoteHost(RemoteHostIP, Port, Username, Password, ProgramName):
    # if return status is 0 - program instaled on remote host
    check_install_program = "which " + str(ProgramName)
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(RemoteHostIP, Port, Username, Password)
    stdin, stdout, stderr = s.exec_command(check_install_program)
    status = stdout.channel.recv_exit_status()
    if status == 0:
        s.close()
        return status
    else:
        s.close()
        return status

def CheckAllNecessarySoftForTest ():
    if SpeedTestParams.cpu_stat:
        if CheckInstallProgramOnRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat') != 0:
            sys.exit(bcolors.FAIL + "[Error in CheckAllNecessarySoftForTest]: " + bcolors.ENDC + " Mpstat not installed on the remote host: " + str(IpAdress.IpSite1))
        if CheckInstallProgramOnRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat') != 0:
            sys.exit(bcolors.FAIL + "[Error in CheckAllNecessarySoftForTest]: " + bcolors.ENDC + " Mpstat not installed on the remote host: " + str(IpAdress.IpSite2))
    if CheckInstallProgramOnRemoteHost(IpAdress.IpRemote, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'netperf') != 0:
        sys.exit(bcolors.FAIL + "[Error in CheckAllNecessarySoftForTest]: " + bcolors.ENDC + " Netperf not installed on the remote host: " + str(IpAdress.IpRemote))
    if CheckInstallProgramOnRemoteHost(IpAdress.IpLocal, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'netperf') != 0:
        sys.exit(bcolors.FAIL + "[Error in CheckAllNecessarySoftForTest]: " + bcolors.ENDC + " Netperf not installed on the remote host: " + str(IpAdress.IpLocal))
    if SpeedTestParams.traf_gen in ('nuttcp', 'ALL'):
        if CheckInstallProgramOnRemoteHost(IpAdress.IpRemote, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'nuttcp') != 0:
            sys.exit(bcolors.FAIL + "[Error in CheckAllNecessarySoftForTest]: " + bcolors.ENDC + " Nuttcp not installed on the remote host: " + str(IpAdress.IpRemote))
        if CheckInstallProgramOnRemoteHost(IpAdress.IpLocal, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'nuttcp') != 0:
            sys.exit(bcolors.FAIL + "[Error in CheckAllNecessarySoftForTest]: " + bcolors.ENDC + " Nuttcp not installed on the remote host: " + str(IpAdress.IpLocal))
    if SpeedTestParams.verbose:
        print bcolors.OKGREEN + "[Info in CheckAllNecessarySoftForTest]: " + bcolors.ENDC + " All necessary soft installed"

def ChangeLspOnRemoteSterraGate (RemoteHostIP, Port, Username, Password, RemoteLSP):
        try:
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(RemoteHostIP, Port, Username, Password, timeout = 3.0)
        except:
            sys.exit(bcolors.FAIL + "[Error in ChangeLspOnRemoteSterraGate]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            check_lsp = 'lsp_mgr check -f ' + str(RemoteLSP)
            if SpeedTestParams.verbose:
                print bcolors.OKGREEN + "[Info in ChangeLspOnRemoteSterraGate]: " + bcolors.ENDC + " Check LSP command: " + str(check_lsp)
            stdin, stdout, stderr = s.exec_command(check_lsp)
            status = stdout.channel.recv_exit_status()
            if status != 0:
                sys.exit(bcolors.FAIL + "[Error in ChangeLspOnRemoteSterraGate]: " + bcolors.ENDC + " Can't check LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP))
            else:
                if status == 0:
                    if SpeedTestParams.verbose:
                        print bcolors.OKGREEN + "[Info in ChangeLspOnRemoteSterraGate]: " + bcolors.ENDC + " Check LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP) + " was successful"
                    load_lsp = 'lsp_mgr load -f ' + str(RemoteLSP)
                    stdin, stdout, stderr = s.exec_command(load_lsp)
                    status = stdout.channel.recv_exit_status()
                    if status !=0:
                        sys.exit(bcolors.FAIL + "[Error in ChangeLspOnRemoteSterraGate]: " + bcolors.ENDC + " Can't load LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP))
                    else:
                        if status == 0:
                            if SpeedTestParams.verbose:
                                print bcolors.OKGREEN + "[Info in ChangeLspOnRemoteSterraGate]: " + bcolors.ENDC + " Load LSP file: " + str(RemoteLSP) + " on remote host: " + str(RemoteHostIP) + " was successful"
        finally:
            s.close()
        return 0

def PutLocalFileToRemoteHost (RemoteHostIP, Port, Username, Password, LocalFile, RemoteFile):
    if os.path.isfile(LocalFile): # check to exitst of local file
        if SpeedTestParams.verbose:
            print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Local file: " + str(LocalFile) + " exists"
        hash_of_local_file = MD5Checksum (LocalFile) # calculate hash of local file
        if SpeedTestParams.verbose:
            print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " MD5 hash: " + str(hash_of_local_file) + " of local file: " + str(LocalFile)
        try:
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(RemoteHostIP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "[Error in PutLocalFileToRemoteHost]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
        else:
            sftp = s.open_sftp()
            try:
                sftp.stat(RemoteFile)
            except IOError:
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Remote file: " + str (RemoteFile) + " on host: " + str (RemoteHostIP) + " does't not exist"
                try:
                    sftp.put(LocalFile, RemoteFile) # if file does't exist on remote host copy local file to remote host
                except IOError:
                    sys.exit(bcolors.FAIL + "[Error in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Can't copy file: " + str(LocalFile) + " to remote host: " + str(RemoteHostIP))
                else:
                    if SpeedTestParams.verbose:
                        print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Local file: " + str (LocalFile) + " was copy to host: " + str (RemoteHostIP) + " its name: " + str(RemoteFile)
                    return 0
            else:
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Remote file: " + str (RemoteFile) + " on host: " + str (RemoteHostIP) + " exist"
                temp_remote_file_on_local_host = os.path.join(os.path.dirname(RemoteFile), "temp_" + os.path.basename(RemoteFile)) # create temp_ suffix for remote file that copy it on local host to calculate md5 hash
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Name of temp file (for remote file) is: " + str (temp_remote_file_on_local_host)
                sftp.get(RemoteFile, temp_remote_file_on_local_host) # get remote file to local host
                hash_of_temp_remote_file = MD5Checksum(temp_remote_file_on_local_host) # calculate md5 hash for temp file
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " MD5 hash: " + str(hash_of_temp_remote_file) + " of temp local file: " + str(temp_remote_file_on_local_host) + " from remote host: " + str(RemoteHostIP)
                if hash_of_local_file == hash_of_temp_remote_file:
                    if SpeedTestParams.verbose:
                        print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " MD5 hashs of: " + str(temp_remote_file_on_local_host) + " and: " + str(LocalFile) + " are same"
                    os.remove(temp_remote_file_on_local_host) # if remote and local files are same - del temp file
                    if SpeedTestParams.verbose:
                        print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Temp file (for remote file): " + str (temp_remote_file_on_local_host) + " was deleted"
                    return 0
                else:
                    if hash_of_local_file != hash_of_temp_remote_file: # if remote and local files are not same
                        if SpeedTestParams.verbose:
                            print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " MD5 hashs of: " + str(temp_remote_file_on_local_host) + " and: " + str(LocalFile) + " are not same"
                        try:
                            sftp.remove(RemoteFile)
                        except:
                            sys.exit(bcolors.FAIL + "[Error in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Can't remove file: " + str(RemoteFile) + " from remote host: " +str(RemoteHostIP))
                        else:
                            if SpeedTestParams.verbose:
                                print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Remote file: " + str (RemoteFile) + " on host: " + str (RemoteHostIP) + " was deleted"
                            os.remove(temp_remote_file_on_local_host)
                            if SpeedTestParams.verbose:
                                print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Temp file (for remote file): " + str (temp_remote_file_on_local_host) + " was deleted"
                            sftp.put(LocalFile, RemoteFile)
                            if SpeedTestParams.verbose:
                                print bcolors.OKGREEN + "[Info in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Local file: " + str(LocalFile) + " was copy to host: " + str(RemoteHostIP) + " its name: " + str(RemoteFile)
                            return 0
        finally:
            s.close()
    else:
        sys.exit(bcolors.FAIL + "[Error in PutLocalFileToRemoteHost]: " + bcolors.ENDC + " Local file: " + str(LocalFile) + " does't exists")

def MD5Checksum(FilePath):
    try:
        file = open(FilePath, 'rb')
    except IOError:
        sys.exit(bcolors.FAIL + "[Error in MD5Checksum]: " + bcolors.ENDC + " Can't open local file: " + str(FilePath))
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

def PutLocalLspToRemoteHost (FirsSiteIP, SecondSiteIP, Port, Username, Password):
    # Put to First site
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, LspFilesClass.first_site_lsp_IMIT, LspFilesClass.first_site_lsp_IMIT)
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, LspFilesClass.first_site_lsp_CI, LspFilesClass.first_site_lsp_CI)
    PutLocalFileToRemoteHost (FirsSiteIP, Port, Username, Password, LspFilesClass.first_site_lsp_C, LspFilesClass.first_site_lsp_C)
    # Put to Second site
    PutLocalFileToRemoteHost (SecondSiteIP, Port, Username, Password, LspFilesClass.second_site_lsp_C_CI_IMIT, LspFilesClass.second_site_lsp_C_CI_IMIT)
    return 0

def ParsingMpstatOutput (MpstatFile,RegExp):
    cpu_idle =[]
    cpu_load = []
    true_cpu_load = []
    mpstat_out_after_not_match_regexp = []
    if os.path.isfile(MpstatFile):
        #open Mpstat output files
        try:
            file = open(MpstatFile, 'r')
        except IOError:
            sys.exit(bcolors.FAIL + "[Error in ParsingMpstatOutput]: " + bcolors.ENDC + " Can't open local file: " + str(MpstatFile))
        else:
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
    else:
        sys.exit(bcolors.FAIL + "[Error in ParsingMpstatOutput]: " + bcolors.ENDC + " Can't check file: " + str(MpstatFile))
    return float(sum(true_cpu_load))/float(len(true_cpu_load))

def GetNumberOfProcessorsOnRemoteHost(RemoteHostIP, Port, Username, Password):
    command_for_finding_number_of_processor = 'cat /proc/cpuinfo | grep proc | wc -l'
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        s.connect(RemoteHostIP, Port, Username, Password)
    except:
        sys.exit(bcolors.FAIL + "[Error in GetNumberOfProcessorsOnRemoteHost]: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
    else:
        stdin, stdout, stderr = s.exec_command(command_for_finding_number_of_processor)
        status = stdout.channel.recv_exit_status()
        if status != 0:
            s.close()
            sys.exit(bcolors.FAIL + "[Error in GetNumberOfProcessorsOnRemoteHost]: " + bcolors.ENDC + " Can't get number of CPUs on remote host: " + str (RemoteHostIP))
        number_of_processor = stdout.read().split()[0]
        if number_of_processor.isdigit():
            s.close()
            if SpeedTestParams.verbose:
                 print bcolors.OKGREEN + "[Info in GetNumberOfProcessorsOnRemoteHost]: " + bcolors.ENDC + " Numbers of CPU: " + str(number_of_processor) + " on remote host: " + str(RemoteHostIP)
            return number_of_processor
        else:
            s.close()
            sys.exit(bcolors.FAIL + "[Error in GetNumberOfProcessorsOnRemoteHost]: " + bcolors.ENDC + " Unknown format number of CPUs on remote host: " + str (RemoteHostIP))

def GetCpuListForMpstat (NunCoresForScatter, NumCoresForEncrypt):
    cpu_list_without_scatter_cores = []
    for i in range(int(NumCoresForEncrypt)):
        # exclude CPU for scatter
        if i not in range (int(NunCoresForScatter)):
            cpu_list_without_scatter_cores.append(str(i))
    # make a list in the form of 1,2,3...
    cpu_list_for_mpstat = ','.join(cpu_list_without_scatter_cores)
    if SpeedTestParams.verbose:
        print bcolors.OKGREEN + "[Info in GetCpuListForMpstat]: " + bcolors.ENDC + " CPU list for Mpstat: " + str(cpu_list_for_mpstat) + ", cores for scatter: " + \
        str (NunCoresForScatter) + ", cores for encrypt: " + str (NumCoresForEncrypt)
    return cpu_list_for_mpstat

def ChoiceCpuListForMpstatDependingOfCpuAffinity (RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile, RegExp):
    if RemoteHostIP == IpAdress.IpSite1:
        NunCoresForScatter, NumCoresForEncrypt = GetCurrentNumOfCoreForScatterAndEncryptOnRemoteSterraGate (RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile, RegExp)
        CpuListForMpstat = GetCpuListForMpstat (NunCoresForScatter, NumCoresForEncrypt)
        return CpuListForMpstat
    if RemoteHostIP == IpAdress.IpSite2:
        NunCoresForScatter, NumCoresForEncrypt = GetCurrentNumOfCoreForScatterAndEncryptOnRemoteSterraGate (RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile, RegExp)
        CpuListForMpstat = GetCpuListForMpstat (NunCoresForScatter, NumCoresForEncrypt)
        return CpuListForMpstat


def GetFilesFromRemoteHost (RemoteHostIP, Port, Username, Password, LocalFile, RemoteFile):
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        s.connect(RemoteHostIP, Port, Username, Password)
    except:
        sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + str(RemoteHostIP) + " Connecting or establishing an SSH session failed")
    else:
        sftp = s.open_sftp()
        try:
            sftp.stat(RemoteFile)
        except IOError:
            s.close()
            sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " File: " + str(RemoteFile) + " does't exist on remote host: " +str(RemoteHostIP))
        else:
            sftp.get(RemoteFile, LocalFile)
        finally:
            s.close()

def NetperfTcpTest (RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = sp.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t TCP_STREAM" + " -i 3,2 " + "-l 30", shell=True, executable='/bin/bash', stdout=sp.PIPE)
    NetperfOtputs = netperf.communicate()[0].splitlines()
    status = netperf.returncode
    if status != 0:
        sys.exit(bcolors.FAIL + "Error :" + bcolors.ENDC + " Netperf can't connect to the netserver " + str(RemoteHostIP) + " from " + str(LocalHostIP))
        print
    throughput_without_loss = NetperfOtputs[-1].split()[-1]
    return throughput_without_loss

def NetperfImixUdpTest(RemHostIP, TestTime):
    Sum = 0.0
    start_imix_test = "netperf -H " + str(RemHostIP) + " -t UDP_STREAM -v 1 -P 0 -p 5001 -l " + str(TestTime) + " -- -m 512 & " \
    + "netperf -H " + str(RemHostIP) + " -t UDP_STREAM -v 1 -P 0 -p 5002 -l " + str(TestTime) + " -- -m 1400 & " \
    + "netperf -H " + str(RemHostIP) + " -t UDP_STREAM -v 1 -P 0 -p 5003 -l " + str(TestTime) + " -- -m 64 & " \
    + "jobs > /dev/null"
    Imix = sp.Popen(start_imix_test, shell=True, executable='/bin/bash', stdout=sp.PIPE) # get stdout from Imix Output (stdout, stderr) = nuttcp.communicate()
    ImixOutputs = Imix.communicate()[0].splitlines()
    status = Imix.returncode
    if (status != 0):
        sys.exit("Error, status is " + str(status))
    for line in ImixOutputs:
        if line == "": #del with output blank lines
            continue
        else:
            if len(line.strip().split()) == 6:
                PacketLength = line.strip().split()[1]
                continue
            else:
                if len(line.strip().split()) == 4:
                    Sum = Sum + float(line.strip().split()[-1])
                    print "PacketLength: ", PacketLength , "Throughput max 10^6bits/sec: ", line.strip().split()[-1]

    print "Sum: ", Sum
    return float(Sum)

def NuttcpUdpTest (Mbps, PacketLength, RemoteHostIP, NumberOfIterations):
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
            if (PingTest(IPlist) != 0) and (count_of_failed_attempts > 0):
                print bcolors.WARNING + "WARNING:" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the warning: remote host " + str(RemoteHostIP) + " Unreachable"
                print 'Attempts to restore the connection ' + str(count_of_failed_attempts)
                print
                time.sleep(3)
                count_of_failed_attempts = count_of_failed_attempts - 1
                continue
            else:
                if (PingTest(IPlist) != 0) and (count_of_failed_attempts <= 0):
                    sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: remote host " + str(RemoteHostIP) + " Unreachable")
                # if host reachable via ICMP and returned status != 0 repeat the last attempts
                if (PingTest(IPlist) == 0) and (flag == 0):
                    flag = 1
                    continue
                else:
                    sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: nuttcp server on the remote host " + str(RemoteHostIP) + " not running")
        speed_without_loss = nuttcpOtputs[-1].split()[6]
        loss_of_current_test = nuttcpOtputs[-1].split()[-2]
        if (float(speed_without_loss) > float(max_speed_without_loss) ):
            max_speed_without_loss = speed_without_loss
        if float(loss_of_current_test) > 1:
            tests_with_loss = tests_with_loss + 1
            max_Mbps_with_loss = Mbps
            Mbps = (float(Mbps) + float(min_Mbps_without_loss)) / 2
        else:
            min_Mbps_without_loss = Mbps
            Mbps = (float(Mbps) + float(max_Mbps_with_loss)) / 2
        i = i - 1
    return speed_without_loss, loss_of_current_test, max_speed_without_loss

def NuttcpTcpTest (RemoteHostIP):
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
            if (PingTest(IPlist) != 0) and (count_of_failed_attempts > 0):
                print bcolors.WARNING + "WARNING:" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the warning: remote host " + str(RemoteHostIP) + " Unreachable"
                print 'Attempts to restore the connection ' + str(count_of_failed_attempts)
                print
                time.sleep(3)
                count_of_failed_attempts = count_of_failed_attempts - 1
                continue
            else:
                if (PingTest(IPlist) != 0) and (count_of_failed_attempts <= 0):
                    sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: remote host " + str(RemoteHostIP) + " Unreachable")
                    # if host reachable via ICMP and returned status != 0 repeat the last attempts
                if (PingTest(IPlist) == 0) and (flag == 0):
                    flag = 1
                    continue
                else:
                    sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " nuttcp can't connect to the nuttcp server. Cause of the error: nuttcp server on the remote host " + str(RemoteHostIP) + " not running")
        else:
            if status == 0:
                break
    speed = nuttcpOtputs[-1].split()[6]
    return speed

def NetperfUdpTest (PacketLength, RemoteHostIP, LocalHostIP):
    NetperfOtputs = []
    netperf = sp.Popen("netperf -H " + str(RemoteHostIP) + " -L " + str(LocalHostIP) + " -t UDP_STREAM" + " -i 3,2 " + "-l 20" + " -- " + " -m " + str(PacketLength) + " -M " \
    + str(PacketLength), shell=True, executable='/bin/bash', stdout=sp.PIPE)
    NetperfOtputs = netperf.communicate()[0].splitlines()
    status = netperf.returncode
    if status != 0:
        sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " Netperf can't connect to the netserver " + str(RemoteHostIP) + " from " + str(LocalHostIP))
        print
    throughput_max = NetperfOtputs[-3].split()[-1]
    throughput_without_loss = NetperfOtputs[-2].split()[-1]
    return throughput_max, throughput_without_loss

def GeneralNetperfImixUdpTestWithMpstat(RemoteHostIP, Port, Username, Password, TestTime):
    #Start Mpstat
    if SpeedTestParams.cpu_stat:
        RestartRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS1)
        RestartRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS2)

    #Start Netperf test
    StopRemoteDaemon (RemoteHostIP, Port, Username, Password, 'netserver')
    time.sleep(0.2)
    StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams (RemoteHostIP, Port, Username, Password, 'netserver', '-p 5001')
    time.sleep(0.2)
    StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams (RemoteHostIP, Port, Username, Password, 'netserver', '-p 5002')
    time.sleep(0.2)
    StartAnotherInstanceOfDaemonOnRemoteHostWithAdditionalParams (RemoteHostIP, Port, Username, Password, 'netserver', '-p 5003')
    time.sleep(0.2)
    print bcolors.HEADER + "Netperf IMIX UDP test with Mpstat " + bcolors.ENDC
    SummTables.table_with_cpu_load[6][1] = NetperfImixUdpTest (RemoteHostIP, TestTime)
    if SpeedTestParams.cpu_stat:
        #Stop Mmstat
        StopRemoteDaemon(IpAdress.IpSite1, Port, Username, Password, 'mpstat')
        StopRemoteDaemon(IpAdress.IpSite2, Port, Username, Password, 'mpstat')
        #Get Mpstat files
        GetFilesFromRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS1, MpstatFilesClass.RemoteFileMpstatS1)
        GetFilesFromRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS2, MpstatFilesClass.RemoteFileMpstatS2)
        #Parse CPU load
        cpu_load_on_site1 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS1, mpstat_header_regexp)
        SummTables.table_with_cpu_load[6][2] = round(cpu_load_on_site1)
        cpu_load_on_site2 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS2, mpstat_header_regexp)
        SummTables.table_with_cpu_load[6][3] = round(cpu_load_on_site2)
        print '{0:.0f}% CPU load on first Site, IP: {1}'.format(cpu_load_on_site1, IpAdress.IpSite1)
        print '{0:.0f}% CPU load on second Site, IP: {1} '.format(cpu_load_on_site2, IpAdress.IpSite2)
    print
    RestartRemoteDaemon (RemoteHostIP, Port, Username, Password, 'netserver')

def GeneralNetperfTcpTestWithMpstat (RemoteHostIP, LocalHostIP):
    #Start Mpstat
    if SpeedTestParams.cpu_stat:
        RestartRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS1)
        RestartRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS2)
    #Start Netperf test
    MaxSpeed = NetperfTcpTest (RemoteHostIP, LocalHostIP)
    print bcolors.HEADER + "Netperf TCP test with Mpstat " + bcolors.ENDC
    print MaxSpeed, "Throughput generated on local host, 10^6bits/sec"
    SummTables.table_with_cpu_load[5][1] = MaxSpeed
    if SpeedTestParams.cpu_stat:
        #Stop Mmstat
        StopRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        StopRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        #Get Mpstat files
        GetFilesFromRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS1, MpstatFilesClass.RemoteFileMpstatS1)
        GetFilesFromRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS2, MpstatFilesClass.RemoteFileMpstatS2)
        #Parse CPU load
        cpu_load_on_site1 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS1, mpstat_header_regexp)
        SummTables.table_with_cpu_load[5][2] = round(cpu_load_on_site1)
        cpu_load_on_site2 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS2, mpstat_header_regexp)
        SummTables.table_with_cpu_load[5][3] = round(cpu_load_on_site2)
        print '{0:.0f}% CPU load on first Site, IP: {1}'.format(cpu_load_on_site1, IpAdress.IpSite1)
        print '{0:.0f}% CPU load on second Site, IP: {1} '.format(cpu_load_on_site2, IpAdress.IpSite2)
    print
    time.sleep(0.5)

def GeneralNuttcpfUdpTestWithMpstat (PacketLength, RemoteHostIP, NumberOfIterations):
    list_of_results_speed = []
    list_of_results_loss = []
    #Start Mpstat
    if SpeedTestParams.cpu_stat:
        RestartRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS1)
        RestartRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS2)
    #Start Nuttcp test
    speed, loss, max_speed_without_loss = NuttcpUdpTest(NuttcpTestParamsClass.StartMbpsForNuttcp, PacketLength, RemoteHostIP, NumberOfIterations)
    print bcolors.HEADER + "Nuttcp UDP test with Mpstat, PacketLength is " + str(PacketLength) + bcolors.ENDC
    print speed, "Throughput"
    print loss, "Loss"
    print
    if SpeedTestParams.cpu_stat:
    #Stop Mmstat
        StopRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        StopRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        #Get Mpstat files
        GetFilesFromRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS1, MpstatFilesClass.RemoteFileMpstatS1)
        GetFilesFromRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS2, MpstatFilesClass.RemoteFileMpstatS2)
        #Parse CPU load
        cpu_load_on_site1 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS1, mpstat_header_regexp)
        cpu_load_on_site2 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS2, mpstat_header_regexp)
        print '{0:.0f}% CPU load on first Site, IP: {1}'.format(cpu_load_on_site1, IpAdress.IpSite1)
        print '{0:.0f}% CPU load on second Site, IP: {1} '.format(cpu_load_on_site2, IpAdress.IpSite2)
    print
    print "Nuttcp UDP test on repeatability of results"
    for i in range(5):
        speed, loss, max_speed_without_loss_temp = NuttcpUdpTest(max_speed_without_loss, PacketLength, RemoteHostIP, 1)
        print
        print "Nuttcp UDP test with Mpstat, PacketLength is ", PacketLength
        print speed, "Throughput"
        print loss, "Loss"
        list_of_results_speed.append(speed)
        list_of_results_loss.append(loss)
    time.sleep(0.5)
    return list_of_results_speed, list_of_results_loss

def GeneralNuttcpTcpTestWithMpstat (RemoteHostIP):
    list_of_results_speed = []
    #Start Mpstat
    if SpeedTestParams.cpu_stat:
        RestartRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS1)
        RestartRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS2)
    #Start Nuttcp test
    speed = NuttcpTcpTest(RemoteHostIP)
    print bcolors.HEADER + "Nuttcp TCP test with Mpstat " + bcolors.ENDC
    print speed, "Throughput without loss"
    if SpeedTestParams.cpu_stat:
        #Stop Mmstat
        StopRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        StopRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        #Get Mpstat files
        GetFilesFromRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS1, MpstatFilesClass.RemoteFileMpstatS1)
        GetFilesFromRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS2, MpstatFilesClass.RemoteFileMpstatS2)
        #Parse CPU load
        cpu_load_on_site1 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS1, mpstat_header_regexp)
        cpu_load_on_site2 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS2, mpstat_header_regexp)
        print '{0:.0f}% CPU load on first Site, IP: {1}'.format(cpu_load_on_site1, IpAdress.IpSite1)
        print '{0:.0f}% CPU load on second Site, IP: {1} '.format(cpu_load_on_site2, IpAdress.IpSite2)
    print

def GeneralNetperfUdpTestWithMpstat (PacketLength, RemoteHostIP, LocalHostIP):
    list_of_results_speed = []
    list_of_results_loss = []
    #Start Mpstat
    if SpeedTestParams.cpu_stat:
        RestartRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS1)
        RestartRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat', "3 -P " + \
        str (ChoiceCpuListForMpstatDependingOfCpuAffinity(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, VpndrvrFilesClass.LocalVpndrvrFile,\
        VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp)), MpstatFilesClass.RemoteFileMpstatS2)
    #Start Netperf test
    MaxSpeed, SpeedWithoutLoss = NetperfUdpTest (PacketLength, RemoteHostIP, LocalHostIP)
    print bcolors.HEADER + "Netperf UDP test with Mpstat, PacketLength is " + str(PacketLength) + bcolors.ENDC
    print MaxSpeed, "Throughput generated on local host, 10^6bits/sec"
    print SpeedWithoutLoss, "Throughput without loss, 10^6bits/sec"

    if PacketLength == 1400:
        SummTables.table_with_cpu_load[1][1] = SpeedWithoutLoss
    if PacketLength == 1000:
        SummTables.table_with_cpu_load[2][1] = SpeedWithoutLoss
    if PacketLength == 512:
        SummTables.table_with_cpu_load[3][1] = SpeedWithoutLoss
    if PacketLength == 64:
        SummTables.table_with_cpu_load[4][1] = SpeedWithoutLoss

    if SpeedTestParams.cpu_stat:
        #Stop Mmstat
        StopRemoteDaemon(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        StopRemoteDaemon(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, 'mpstat')
        #Get Mpstat files
        GetFilesFromRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS1, MpstatFilesClass.RemoteFileMpstatS1)
        GetFilesFromRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, MpstatFilesClass.LocalFileMpstatS2, MpstatFilesClass.RemoteFileMpstatS2)
        #Parse CPU load
        cpu_load_on_site1 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS1, mpstat_header_regexp)
        cpu_load_on_site2 = ParsingMpstatOutput(MpstatFilesClass.LocalFileMpstatS2, mpstat_header_regexp)
        if PacketLength == 1400:
            SummTables.table_with_cpu_load[1][2] = round(cpu_load_on_site1)
            SummTables.table_with_cpu_load[1][3] = round(cpu_load_on_site2)
        if PacketLength == 1000:
            SummTables.table_with_cpu_load[2][2] = round(cpu_load_on_site1)
            SummTables.table_with_cpu_load[2][3] = round(cpu_load_on_site2)
        if PacketLength == 512:
            SummTables.table_with_cpu_load[3][2] = round(cpu_load_on_site1)
            SummTables.table_with_cpu_load[3][3] = round(cpu_load_on_site2)
        if PacketLength == 64:
            SummTables.table_with_cpu_load[4][2] = round(cpu_load_on_site1)
            SummTables.table_with_cpu_load[4][3] = round(cpu_load_on_site2)
        print '{0:.0f}% CPU load on first Site, IP: {1}'.format(cpu_load_on_site1, IpAdress.IpSite1)
        print '{0:.0f}% CPU load on second Site, IP: {1} '.format(cpu_load_on_site2, IpAdress.IpSite2)
    print
    time.sleep(1)

#Nuttcp test with Mpstat
def FullNuttcpTestWithMpstat ():
    for attempts in range(SpeedTestParams.iterations):
        avg_speed_UDP1400, avg_loss_UDP1400 = GeneralNuttcpfUdpTestWithMpstat (NuttcpTestParamsClass.UDP1400, IpAdress.IpRemote, NuttcpTestParamsClass.IterationsForRepeatTest)
        avg_speed_UDP1000, avg_loss_UDP1000 = GeneralNuttcpfUdpTestWithMpstat (NuttcpTestParamsClass.UDP1000, IpAdress.IpRemote, NuttcpTestParamsClass.IterationsForRepeatTest)
        avg_speed_UDP512, avg_loss_UDP512 = GeneralNuttcpfUdpTestWithMpstat (NuttcpTestParamsClass.UDP512, IpAdress.IpRemote, NuttcpTestParamsClass.IterationsForRepeatTest)
        avg_speed_UDP64, avg_loss_UDP64 = GeneralNuttcpfUdpTestWithMpstat (NuttcpTestParamsClass.UDP64, IpAdress.IpRemote, NuttcpTestParamsClass.IterationsForRepeatTest)
        GeneralNuttcpTcpTestWithMpstat (IpAdress.IpRemote)
        print bcolors.HEADER + "Average result for Nuttcp tests" + bcolors.ENDC
        print
        print bcolors.OKBLUE + "UDP1400 speed is" + str(avg_speed_UDP1400) + " loss is " + str(avg_loss_UDP1400) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP1000 speed is" + str(avg_speed_UDP1000) + " loss is " + str(avg_loss_UDP1000) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP512 speed is" + str(avg_speed_UDP512) + " loss is " + str(avg_loss_UDP512) + bcolors.ENDC
        print bcolors.OKBLUE + "UDP64 speed is" + str(avg_speed_UDP64) + " loss is " + str(avg_loss_UDP64) + bcolors.ENDC
        print

#Netperf test with Mpstat
def FullNetperfTestWithMpstat ():
    for attempt in range(SpeedTestParams.iterations):
        GeneralNetperfUdpTestWithMpstat (NetperfTestParamsClass.UDP1400, IpAdress.IpRemote, IpAdress.IpLocal)
        GeneralNetperfUdpTestWithMpstat (NetperfTestParamsClass.UDP1000, IpAdress.IpRemote, IpAdress.IpLocal)
        GeneralNetperfUdpTestWithMpstat (NetperfTestParamsClass.UDP512, IpAdress.IpRemote, IpAdress.IpLocal)
        GeneralNetperfUdpTestWithMpstat (NetperfTestParamsClass.UDP64, IpAdress.IpRemote, IpAdress.IpLocal)
        GeneralNetperfTcpTestWithMpstat (IpAdress.IpRemote, IpAdress.IpLocal)
        GeneralNetperfImixUdpTestWithMpstat(IpAdress.IpRemote, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, NetperfTestParamsClass.TimeForImixTest)
        out = sys.stdout
        pprint_table(out, SummTables.table_with_cpu_load)

def SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate (RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile, RegExp, NumCoreForScatter, NunCoreForEncrypt, SummCoreOnRemoSterraGate):
    CpuDistributionOnRemoteSterraGate = False
    # chech correct of CPU affinity
    if int(NumCoreForScatter) + int(NunCoreForEncrypt) <= int(SummCoreOnRemoSterraGate):
        if SpeedTestParams.verbose:
            print bcolors.OKGREEN + "[Info in SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " Check of CPU affinity was successful on remote host: " + str (RemoteHostIP)
        # get remote vpndrvr.conf file
        GetFilesFromRemoteHost( RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile)
        # read local vpndrvr.conf file
        file = open(LocalVpndrvrFile, 'r')
        vpndrvr_conf = file.readlines()
        for line in vpndrvr_conf: # see all line in local vpndrvr.conf file
            if RegExp.match(line):
                CpuDistributionOnRemoteSterraGate = True # set CpuDistributionOnRemoteSterraGate = True if CPU affinity did set on remote host before
                NumScatterCoresBeforeReplacment = RegExp.match(line).group(1) # get core for scatter before replacment
                NumEncryptCoresBeforeReplacment = RegExp.match(line).group(2) # get core for encrypt before replacment
                if SpeedTestParams.verbose:
                    print bcolors.OKGREEN + "[Info in SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " CPU affinity on remote host: " + str(RemoteHostIP) + " before replacement: options vpndrvr cpu_distribution=\"*:" + \
                    str(NumScatterCoresBeforeReplacment) + "/" +  str(NumEncryptCoresBeforeReplacment) + "\""
        if not CpuDistributionOnRemoteSterraGate: # if CPU affinity didn't set on remote host
            if SpeedTestParams.verbose:
                print bcolors.OKGREEN + "[Info in SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " CPU affinity on remote host: " + str(RemoteHostIP) + " didn't set before change"
            file = open(LocalVpndrvrFile, 'a+') # append to end
            file.writelines("options vpndrvr cpu_distribution=\"*:" + str(NumCoreForScatter)+ "/" +  str(NunCoreForEncrypt) + "\"\n")
            file.close()
            PutLocalFileToRemoteHost (RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile)
            if SpeedTestParams.verbose:
                print bcolors.OKGREEN + "[Info in SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " New CPU affinity write on local file: " + str (LocalVpndrvrFile) + \
                ", current CPU affinity: options vpndrvr cpu_distribution=\"*:" + str(NumCoreForScatter)+ "/" +  str(NunCoreForEncrypt) + "\""
            os.remove(LocalVpndrvrFile)
            RestartRemoteSterraGate (RemoteHostIP, Port, Username, Password)
        else:
            if CpuDistributionOnRemoteSterraGate:
                # if current affinity are same with what you want  - do nothing
                if (int(NumScatterCoresBeforeReplacment) == int(NumCoreForScatter) ) and (int (NumEncryptCoresBeforeReplacment) == int(NunCoreForEncrypt)):
                    print bcolors.OKGREEN + "[Info in SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " CPU affinity don't change, on host: " + str(RemoteHostIP) + ", because current affinity are same with what you want"
                    file.close()
                    os.remove(LocalVpndrvrFile)
                    RestartRemoteSterraGate (RemoteHostIP, Port, Username, Password)
                    return 1
                else:
                    file = open(LocalVpndrvrFile, 'r+')
                    for line in vpndrvr_conf:
                        if not RegExp.match(line):
                            file.writelines(line)
                        else:
                            file.writelines("options vpndrvr cpu_distribution=\"*:" + str(NumCoreForScatter)+ "/" +  str(NunCoreForEncrypt) + "\"\n")
                    file.close()
                    if SpeedTestParams.verbose:
                        print bcolors.OKGREEN + "[Info in SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " New CPU affinity write on local file: " + str (LocalVpndrvrFile) + \
                        ", current CPU affinity: options vpndrvr cpu_distribution=\"*:" + str(NumCoreForScatter)+ "/" +  str(NunCoreForEncrypt) + "\""
                    # copy local vpndrvr.conf file to remote host
                    PutLocalFileToRemoteHost (RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile)
                    os.remove(LocalVpndrvrFile)
                    RestartRemoteSterraGate (RemoteHostIP, Port, Username, Password)
    else:
        sys.exit(bcolors.FAIL + "[Error in SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate]:" + bcolors.ENDC + " Check of CPU affinity was fail on remote host: " + str(RemoteHostIP) + ", because cores for scatter + cores for encrypt > number of cores on host")

def GetCurrentNumOfCoreForScatterAndEncryptOnRemoteSterraGate (RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile, RegExp):
    CpuDistributionOnRemoteSterraGate = False
    # get remote vpndrvr.conf file
    GetFilesFromRemoteHost( RemoteHostIP, Port, Username, Password, LocalVpndrvrFile, RemoteVpndrvrFile)
    # read local vpndrvr.conf file
    file = open(LocalVpndrvrFile, 'r')
    vpndrvr_conf = file.readlines()
    for line in vpndrvr_conf: # see all line in local vpndrvr.conf file
        if RegExp.match(line):
            CpuDistributionOnRemoteSterraGate = True # set CpuDistributionOnRemoteSterraGate = True if CPU affinity did set on remote host before
            CurrentNumScatterCores = RegExp.match(line).group(1) # get current cores for scatter
            CurrenNumEncryptCores = RegExp.match(line).group(2) # get current cores for encrypt
            if SpeedTestParams.verbose:
                print bcolors.OKGREEN + "[Info in GetCurrentNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " CPU affinity on remote host: " + str(RemoteHostIP) + ", affinity: options vpndrvr cpu_distribution=\"*:" + \
                str(CurrentNumScatterCores) + "/" +  str(CurrenNumEncryptCores) + "\""
            file.close()
            os.remove(LocalVpndrvrFile)
            return CurrentNumScatterCores, CurrenNumEncryptCores
    if not CpuDistributionOnRemoteSterraGate: # if CPU affinity didn't set on remote host
        if SpeedTestParams.verbose:
            print bcolors.OKGREEN + "[Info in GetCurrentNumOfCoreForScatterAndEncryptOnRemoteSterraGate]: " + bcolors.ENDC + " CPU affinity on remote host: " + str(RemoteHostIP) + " didn't set"
        file.close()
        os.remove(LocalVpndrvrFile)
        return 1, int(GetNumberOfProcessorsOnRemoteHost(RemoteHostIP, Port, Username, Password)) - 1


def ChoseTest ():
    if (SpeedTestParams.encrypt_alg == 'C') and (SpeedTestParams.traf_gen == 'netperf'):
        FullNetperfTestWithMpstat_C ()
    if (SpeedTestParams.encrypt_alg == 'CI') and (SpeedTestParams.traf_gen == 'netperf'):
        FullNetperfTestWithMpstat_CI ()
    if (SpeedTestParams.encrypt_alg == 'IMIT') and (SpeedTestParams.traf_gen == 'netperf'):
        FullNetperfTestWithMpstat_IMIT ()
    if (SpeedTestParams.encrypt_alg == 'ALL') and (SpeedTestParams.traf_gen == 'netperf'):
        FullNetperfTestWithMpstat_ALL ()
    if (SpeedTestParams.encrypt_alg == 'C') and (SpeedTestParams.traf_gen == 'nuttcp'):
        FullNuttcpfTestWithMpstat_C ()
    if (SpeedTestParams.encrypt_alg == 'CI') and (SpeedTestParams.traf_gen == 'nuttcp'):
        FullNuttcpfTestWithMpstat_CI ()
    if (SpeedTestParams.encrypt_alg == 'IMIT') and (SpeedTestParams.traf_gen == 'nuttcp'):
        FullNuttcpfTestWithMpstat_IMIT ()
    if (SpeedTestParams.encrypt_alg == 'ALL') and (SpeedTestParams.traf_gen == 'nuttcp'):
        FullNuttcpfTestWithMpstat_ALL ()
    if (SpeedTestParams.encrypt_alg == 'ALL') and (SpeedTestParams.traf_gen == 'ALL'):
        FullNuttcpfAndNetperfTestWithMpstat_ALL ()
    if (SpeedTestParams.encrypt_alg == 'C') and (SpeedTestParams.traf_gen == 'ALL'):
        FullNuttcpfAndNetperfTestWithMpstat_C ()
    if (SpeedTestParams.encrypt_alg == 'CI') and (SpeedTestParams.traf_gen == 'ALL'):
        FullNuttcpfAndNetperfTestWithMpstat_CI ()
    if (SpeedTestParams.encrypt_alg == 'IMIT') and (SpeedTestParams.traf_gen == 'ALL'):
        FullNuttcpfAndNetperfTestWithMpstat_IMIT ()
    # no LSP tests
    if (SpeedTestParams.encrypt_alg == 'NOLSP') and (SpeedTestParams.traf_gen == 'ALL'):
        FullNuttcpfAndNetperfTestWithMpstat_NOLSP ()
    if (SpeedTestParams.encrypt_alg == 'NOLSP') and (SpeedTestParams.traf_gen == 'nuttcp'):
        FullNuttcpfTestWithMpstat_NOLSP ()
    if (SpeedTestParams.encrypt_alg == 'NOLSP') and (SpeedTestParams.traf_gen == 'netperf'):
        FullNetperfTestWithMpstat_NOLSP ()

def FullNetperfTestWithMpstat_C ():
        print bcolors.HEADER + "**********Start test CIPHER with Netperf (Mpstat)**********" + bcolors.ENDC
        ChangeLspOnRemoteSterraGate (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, LspFilesClass.first_site_lsp_C)
        SummTables.table_with_cpu_load[0][0] = "Netperf, Cipher"
        FullNetperfTestWithMpstat()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNetperfTestWithMpstat_CI ():
        print bcolors.HEADER + "**********Start test CIPHER and INTEGRITY with Netperf (Mpstat)**********" + bcolors.ENDC
        ChangeLspOnRemoteSterraGate (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, LspFilesClass.first_site_lsp_CI)
        SummTables.table_with_cpu_load[0][0] = "Netperf, Cipher and Int"
        FullNetperfTestWithMpstat()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNetperfTestWithMpstat_IMIT ():
        print bcolors.HEADER + "**********Start test IMIT with Netperf (Mpstat)**********" + bcolors.ENDC
        ChangeLspOnRemoteSterraGate (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, LspFilesClass.first_site_lsp_IMIT)
        SummTables.table_with_cpu_load[0][0] = "Netperf, Imit"
        FullNetperfTestWithMpstat()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNetperfTestWithMpstat_ALL ():
        print bcolors.HEADER + "**********Start tests C and CI and IMIT with Netperf (Mpstat)**********" + bcolors.ENDC
        FullNetperfTestWithMpstat_C ()
        FullNetperfTestWithMpstat_CI ()
        FullNetperfTestWithMpstat_IMIT ()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_C ():
        print bcolors.HEADER + "**********Start test CIPHER with Nuttcp (Mpstat)**********" + bcolors.ENDC
        ChangeLspOnRemoteSterraGate (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, LspFilesClass.first_site_lsp_C)
        FullNuttcpTestWithMpstat()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_CI ():
        print bcolors.HEADER + "**********Start test CIPHER and INTEGRITY with Nuttcp (Mpstat)**********" + bcolors.ENDC
        ChangeLspOnRemoteSterraGate (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, LspFilesClass.first_site_lsp_CI)
        FullNuttcpTestWithMpstat()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_IMIT ():
        print bcolors.HEADER + "**********Start test IMIT with Nuttcp (Mpstat)**********" + bcolors.ENDC
        ChangeLspOnRemoteSterraGate (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, LspFilesClass.first_site_lsp_IMIT)
        FullNuttcpTestWithMpstat()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_ALL ():
        print bcolors.HEADER + "**********Start tests C and CI and IMIT with Nuttcp (Mpstat)**********" + bcolors.ENDC
        FullNuttcpfTestWithMpstat_C ()
        FullNuttcpfTestWithMpstat_CI ()
        FullNuttcpfTestWithMpstat_IMIT ()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfAndNetperfTestWithMpstat_ALL ():
        print bcolors.HEADER + "**********Start tests C and CI and IMIT with Nuttcp and Netperf (Mpstat)**********" + bcolors.ENDC
        FullNuttcpfTestWithMpstat_ALL ()
        FullNetperfTestWithMpstat_ALL ()

def FullNuttcpfAndNetperfTestWithMpstat_C ():
        print bcolors.HEADER + "**********Start test CIPHER with Nuttcp and Netperf (Mpstat)**********" + bcolors.ENDC
        FullNetperfTestWithMpstat_C ()
        FullNuttcpfTestWithMpstat_C ()

def FullNuttcpfAndNetperfTestWithMpstat_CI ():
        print bcolors.HEADER + "**********Start test CIPHER and INTEGRITY with Nuttcp and Netperf (Mpstat)**********" + bcolors.ENDC
        FullNetperfTestWithMpstat_CI ()
        FullNuttcpfTestWithMpstat_CI ()

def FullNuttcpfAndNetperfTestWithMpstat_IMIT ():
        print bcolors.HEADER + "**********Start test IMIT with Nuttcp and Netperf (Mpstat)**********" + bcolors.ENDC
        FullNetperfTestWithMpstat_IMIT ()
        FullNuttcpfTestWithMpstat_IMIT ()

def FullNuttcpfAndNetperfTestWithMpstat_NOLSP ():
        print bcolors.HEADER + "**********Start test NOLSP with Nuttcp and Netperf (Mpstat)**********" + bcolors.ENDC
        FullNetperfTestWithMpstat ()
        FullNuttcpTestWithMpstat ()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNuttcpfTestWithMpstat_NOLSP ():
        print bcolors.HEADER + "**********Start test NOLSP with Nuttcp (Mpstat)**********" + bcolors.ENDC
        FullNuttcpTestWithMpstat ()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC

def FullNetperfTestWithMpstat_NOLSP ():
        print bcolors.HEADER + "**********Start test NOLSP with Netperf (Mpstat)**********" + bcolors.ENDC
        FullNetperfTestWithMpstat ()
        print bcolors.HEADER + "****************************************************************" + bcolors.ENDC
try:
    # create exemplar of IpAdressClass()
    IpAdress = IpAdressClass()
    # create exemplar of SpeedTestParamsClass ()
    SpeedTestParams = SpeedTestParamsClass ()
    # parse parametrs of script
    ParsingParametrsOfScript ()
    # ping test
    if PingTest(IpAdress.GetIpList()) == 0:
        if SpeedTestParams.verbose:
            print bcolors.OKGREEN + "[Info in Main]: " + bcolors.ENDC + " Network test complete successfully"
    # chech installed soft
    CheckAllNecessarySoftForTest ()
    # set CPU affinity
    if SpeedTestParams.cpu_aff_on_site1:
        SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, \
        VpndrvrFilesClass.LocalVpndrvrFile, VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp, SpeedTestParams.number_cpu_for_scatter_on_site1, \
        SpeedTestParams.number_cpu_for_encrypt_on_site1, GetNumberOfProcessorsOnRemoteHost(IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password))
    if SpeedTestParams.cpu_aff_on_site2:
        SetNumOfCoreForScatterAndEncryptOnRemoteSterraGate (IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password, \
        VpndrvrFilesClass.LocalVpndrvrFile, VpndrvrFilesClass.RemoteVpndrvrFile, vpndrvr_cpu_distribution_regexp, SpeedTestParams.number_cpu_for_scatter_on_site2, \
        SpeedTestParams.number_cpu_for_encrypt_on_site2, GetNumberOfProcessorsOnRemoteHost(IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password))
    # sync time
    if SpeedTestParams.time_sync_on_sites:
        SetTimeOnRemoteHostAsLocalHost (IpAdress.IpSite1, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password)
        SetTimeOnRemoteHostAsLocalHost (IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password)
    # print summary table
    PrintSummaryOfTest ()
    # copy local LSP to Sites if encryp alg not NOLSP
    if SpeedTestParams.encrypt_alg != 'NOLSP' :
        PutLocalLspToRemoteHost (IpAdress.IpSite1, IpAdress.IpSite2, SshConParamsClass.port, SshConParamsClass.username, SshConParamsClass.password)
    else:
        if SpeedTestParams.verbose:
            print bcolors.OKGREEN + "[Info in Main]: " + bcolors.ENDC + " Chose NOLSP test"
    # chose test
    ChoseTest ()
except KeyboardInterrupt:
    sys.exit(bcolors.OKGREEN + "[Info in Main]: " + bcolors.ENDC + " Test was stopped")