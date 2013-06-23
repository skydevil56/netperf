#!/usr/bin/python
# Args:
#   1: packet length
#   2: username
#   3: command to run
import sys
import warnings
import subprocess
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko
	
port = 22
hostname_s1 = '192.168.7.2'
hostname_s2 = '192.168.8.2'
s1_ip = '192.168.7.1'
s2_ip = '192.168.8.1'
username = 'root'
password = 'russia'
NetperfOtputs = []
vmstat_s1 = []
vmstat_s2 = []
out_vmstat_s1 = []
out_vmstat_s2 = []
temp_s1 = []
temp_s2 = []

paramiko.util.log_to_file('paramiko.log')
s1 = paramiko.SSHClient()
s1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s1.connect(hostname_s1, port, username, password)
#stdin, stdout, stderr = s1.exec_command(kill_vmstat_on_s1)
stdin, stdout, stderr = s1.exec_command('vmstat 2 -n > vmstat_s1 &')
stdin, stdout, stderr = s1.exec_command('ps -A | grep vmstat')
pid_vmstat_s1 = stdout.read().split()[0]
kill_vmstat_on_s1 = "kill" + " " + str(pid_vmstat_s1)
print "pid vmstat on s1 is", pid_vmstat_s1
#stdin.write('\n')


s2 = paramiko.SSHClient()
s2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s2.connect(hostname_s2, port, username, password)
#stdin, stdout, stderr = s2.exec_command(kill_vmstat_on_s2)
stdin, stdout, stderr = s2.exec_command('vmstat 2 -n > vmstat_s2 &')
stdin, stdout, stderr = s2.exec_command('ps -A | grep vmstat')
pid_vmstat_s2 = stdout.read().split()[0]
kill_vmstat_on_s2 = "kill" + " " + str(pid_vmstat_s2)
print "pid vmstat on s2 is", pid_vmstat_s2

print '\n'
print "Test is running, please wait..."

netperf = subprocess.Popen("netperf -H " + str(s2_ip) + " -L " + str(s1_ip) + " -t UDP_STREAM" + " -i 5,5 " + "-l 20" + " -- " + " -m " + str(sys.argv[1]) + " -M " + str(sys.argv[1]), shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
NetperfOtputs = netperf.stdout.readlines()

ftp_s1 = s1.open_sftp()
ftp_s1.get('/root/vmstat_s1', '/root/vmstat_s1')
ftp_s2 = s2.open_sftp()
ftp_s2.get('/root/vmstat_s2', '/root/vmstat_s2')

#beegin //////////////parsing CPU load

# open file vmstat_s1
file_s1 = open('vmstat_s1', 'r')
vmstat_s1 = file_s1.readlines()
#head not read
for line in vmstat_s1[3:-1:]:
#parsing CPU load and add to list
    temp_s1.append(float(line.split()[13]))

#delete zeros ans ones
if temp_s1.count(0.0) != 0:
    for i in range(temp_s1.count(0.0)):
        temp_s1.remove(0.0)

if temp_s1.count(1.0) != 0:
    for i in range(temp_s1.count(1.0)):
        temp_s1.remove(1.0)

#find average
avg = sum(temp_s1)/float(len(temp_s1))

#create new list where items > avg
for i in temp_s1:
    if i > avg:
        out_vmstat_s1.append(i) 

# open file vmstat_s2
file_s2 = open('vmstat_s2', 'r')
vmstat_s2 = file_s2.readlines()
#head not read
for line in vmstat_s2[3:-1:]:
#parsing CPU load and add to list
    temp_s2.append(float(line.split()[13]))

#delete zeros ans ones
if temp_s2.count(0.0) != 0:
    for i in range(temp_s2.count(0.0)):
        temp_s2.remove(0.0)

if temp_s2.count(1.0) != 0:
    for i in range(temp_s2.count(1.0)):
        temp_s2.remove(1.0)

#find average
avg = sum(temp_s2)/float(len(temp_s2))

#create new list where items > avg
for i in temp_s2:
    if i > avg:
        out_vmstat_s2.append(i) 

#end //////////////parsing CPU load

print '\n'
print NetperfOtputs[-3].split()[-1], "Throughput max 10^6bits/sec"
print NetperfOtputs[-2].split()[-1], "Throughput without loss 10^6bits/sec"

print '\n'
#print out_vmstat_s1
print sum(out_vmstat_s1)/float(len(out_vmstat_s1)), "CPU load on Site_1"
#print out_vmstat_s2
print sum(out_vmstat_s2)/float(len(out_vmstat_s2)), "CPU load on Site_2"

stdin, stdout, stderr = s1.exec_command(kill_vmstat_on_s1)
stdin, stdout, stderr = s2.exec_command(kill_vmstat_on_s2)

file_s1.close()
s1.close()
s2.close()
ftp_s1.close()
ftp_s2.close()