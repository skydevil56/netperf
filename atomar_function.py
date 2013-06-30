#!/usr/bin/python

import sys, getopt
import time
import re
import warnings
import subprocess as sp
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko

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

if RestartRemoteDaemon ('192.168.7.1', 22, 'root', 'russia', 'vmstat', '2 -n', '/root/vmstat_output_test') == 0:
    print "restart remote daemon vmstat was OK"
else:
    print "restart remote daemon vmstat ERROR"

if RestartLocalDaemon ('vmstat', '2 -n', '/root/vmstat_output_test') == 0:
    print "restart local daemon vmstat was OK"
else:
    print "restart local daemon vmstat ERROR"