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
import optparse


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
    cpu_aff_on_site2 = False
    number_cpu_for_scatter_on_site1 = 1
    number_cpu_for_encrypt_on_site1 = 1
    number_cpu_for_scatter_on_site2 = 1
    number_cpu_for_encrypt_on_site2 = 1
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
parser.add_option('--ip_local', help='Local traffic generator machine IP', dest='ip_local', action='store', metavar='{IPv4 address}')
parser.add_option('--ip_remote', help='Remote traffic receiver machine IP', dest='ip_remote', action='store', metavar='{IPv4 address}')
parser.add_option('--ip_site1', help='First IPsec Site IP', dest='ip_site1', action='store', metavar='{IPv4 address}')
parser.add_option('--ip_site2', help='Second IPsec Site IP', dest='ip_site2', action='store', metavar='{IPv4 address}')
parser.add_option('--encr_alg', help='Encryption algorithm. A default value [%default]', dest='encr_alg', action='store', metavar='{C | CI | IMIT | ALL | NOLSP}', default='NOLSP')
parser.add_option('--traf_gen', help='Traffic generator. A default value [%default]', dest='traf_gen', action='store', metavar='{nuttcp | netperf | ALL}', default='netperf')
parser.add_option('--iterations', help='Test iterations. A default value [%default]', dest='iterations', action='store', metavar='{integer}', type='int', default=1)
parser.add_option('--time_sync_on_sites', help='Time syncr on two IPsec Sites. A default value [%default]', dest='time_sync_on_sites', default=False, action='store_true')
parser.add_option('--cpu_aff_on_site1', help='Set CPU affinity on first IPsec Site. A default value [%default]', dest='cpu_aff_on_site1', default=False, action='store', metavar='{{int},{int}}', nargs=2, type='int')
parser.add_option('--cpu_aff_on_site2', help='Set CPU affinity on second IPsec Site. A default value [%default]', dest='cpu_aff_on_site2', default=False, action='store', metavar='{{int},{int}}', nargs=2, type='int')
(opts, args) = parser.parse_args()

IpAdress = IpAdressClass()
SpeedTestParams = SpeedTestParamsClass ()

IpAdress.IpLocal = opts.ip_local
IpAdress.IpRemote = opts.ip_remote
IpAdress.IpSite1 = opts.ip_site1
IpAdress.IpSite2 = opts.ip_site2
if not opts.encr_alg:
    SpeedTestParams.encrypt_alg = 'NOLSP'
else:
    SpeedTestParams.encrypt_alg = opts.encr_alg
if not opts.traf_gen:
    SpeedTestParams.traf_gen = 'netperf'
else:
    SpeedTestParams.traf_gen = opts.traf_gen
if not opts.time_sync_on_sites:
    SpeedTestParams.time_sync_on_sites = False
else:
    SpeedTestParams.time_sync_on_sites = opts.time_sync_on_sites
if not opts.cpu_aff_on_site1:
    SpeedTestParams.cpu_aff_on_site1 = False
else:
    SpeedTestParams.SetNumberCpuForScatterOnSite1(opts.cpu_aff_on_site1[0])
    SpeedTestParams.SetNumberCpuForEncryptOnSite1(opts.cpu_aff_on_site1[1])
if not opts.cpu_aff_on_site2:
    SpeedTestParams.cpu_aff_on_site2 = False
else:
    SpeedTestParams.SetNumberCpuForScatterOnSite2(opts.cpu_aff_on_site2[0])
    SpeedTestParams.SetNumberCpuForEncryptOnSite2(opts.cpu_aff_on_site2[1])
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
    print 'CPU aff. on Site 1:              ', SpeedTestParams.cpu_aff_on_site1
    if SpeedTestParams.cpu_aff_on_site1 == True:
        print '     Num. CPU for scatter on Site 1: ', SpeedTestParams.number_cpu_for_scatter_on_site1
        print '     Num. CPU for encrypt on Site 1: ', SpeedTestParams.number_cpu_for_encrypt_on_site1
    print 'CPU aff. on Site 2:              ', SpeedTestParams.cpu_aff_on_site2
    if SpeedTestParams.cpu_aff_on_site2 == True:
        print '     Num. CPU for scatter on Site 2: ', SpeedTestParams.number_cpu_for_scatter_on_site2
        print '     Num. CPU for encrypt on Site 2: ', SpeedTestParams.number_cpu_for_encrypt_on_site2
    print 'Number of iterations:            ', SpeedTestParams.iterations
PrintSummaryOfTest ()