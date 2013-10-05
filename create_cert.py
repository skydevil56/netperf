#!/usr/bin/python
import os, sys, time, optparse, warnings
import subprocess as sp

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

desc = "Create remote certificate for S-Terra Gate 4.1"
parser = optparse.OptionParser(description=desc)
parser.add_option('--create_cert', help='Create cert. A default value [%default]', dest='create_cert', default=False, action='store_true')
parser.add_option('--cert_and_cont_name', help='Certificate and container name. A default value [%default]', dest='cert_and_cont_name', action='store', metavar='{Certificate and container name}', default='GwCert')
parser.add_option('--path_of_gamma', help='Path of gamma of CryptoPro (for one files: /db2/kis_1 or /db1/kis_1 - are same )', dest='path_of_gamma', action='store', metavar='{Path of gamma of CryptoPro}')
parser.add_option('--path_of_ca_cert', help='Path of CA certificate', dest='path_of_ca_cert', action='store', metavar='{Path of CA certificate}')
parser.add_option('--ip_ca', help='IP address of CA', dest='ip_ca', action='store', metavar='{IP address of CA}')
parser.add_option('--ip_remote_host', help='IP address of remote host', dest='ip_remote_host', action='store', metavar='{IP address of remote host}')
parser.add_option('--ssh_username', help='SSH username. A default value [%default]', dest='ssh_username', action='store', default='root', metavar='{SSH username}')
parser.add_option('--ssh_pass', help='SSH password. A default value [%default]', dest='ssh_pass', action='store', default='russia', metavar='{SSH password}')
parser.add_option('--arch_on_remote_host', help='Architecture on remote host', dest='arch_on_remote_host', action='store', metavar='{64 | 86}', type = 'int')
##parser.add_option('--copy_remote_cert', help='Copy remote certificate on local hosr. A default value [%default]', dest='copy_remote_cert', default=False, action='store_true')
##parser.add_option('--path_for_remote_cert', help='Path of remote certificate', dest='path_for_remote_cert', action='store', metavar='{Path of remote certificate}')
##parser.add_option('--parameters_from_file', help='Get parameters from file. A default value [%default]', dest='parameters_from_file', default=False, action='store_true')
##parser.add_option('--path_of_parameters', help='Path of parameters (ip, username, password, cert_name, arch,)', dest='path_of_parameters', action='store', metavar='{Path of parameters}')
parser.add_option('--verbose', help='More information during the test. A default value [%default]', dest='verbose', default=False, action='store_true')
(opts, args) = parser.parse_args()

class parametersForEnrollCert:
    CreateCert = False
    NameOfCertAndContainer = ''
    PathOfGamma = ''
    PathOfCaCert = ''
    IpOfMsCa = ''
    IpOfRemoteHost = ''
    SshUsernameForRemoteHost = ''
    SshPassForRemoteHost = ''
    ArchOfRemoteHost = ''
    CopyRemoteCertToLocalHost = False
    PathForRemoteCertOnLocalHost = ''
    GetParametersFromFile = False
    PathOfRemoteConnectionparameters = ''
    Verbose =  False
    Path1OfGammaOnRemoteHost = '/var/opt/cprocsp/dsrf/db1/kis_1'
    Path2OfGammaOnRemoteHost = '/var/opt/cprocsp/dsrf/db2/kis_1'

def ParsingparametersOfScript ():
##    if opts.create_cert and opts.parameters_from_file:
##        sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " --cert_create and --parameters_from_file can not be together")

    # check all required parameters for --create_cert
    if opts.create_cert and  (( opts.cert_and_cont_name is None) or ( opts.path_of_gamma is None) or (opts.path_of_ca_cert is None) \
    or (opts.arch_on_remote_host is None) or (opts.ip_ca is None) or (opts.ip_remote_host is None) or (opts.ssh_username is None) or (opts.ssh_pass is None)):
        sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " Not all parameters for create certificate")
    else:
        parametersForEnrollCert.CreateCert = opts.create_cert
        parametersForEnrollCert.NameOfCertAndContainer = opts.cert_and_cont_name
        parametersForEnrollCert.PathOfGamma = opts.path_of_gamma
        parametersForEnrollCert.PathOfCaCert = opts.path_of_ca_cert
        parametersForEnrollCert.ArchOfRemoteHost = opts.arch_on_remote_host
        parametersForEnrollCert.IpOfMsCa = opts.ip_ca
        parametersForEnrollCert.IpOfRemoteHost = opts.ip_remote_host
        parametersForEnrollCert.SshUsernameForRemoteHost = opts.ssh_username
        parametersForEnrollCert.SshPassForRemoteHost = opts.ssh_pass
        # check required parameter for --copy_remote_cert
        if opts.copy_remote_cert and (opts.path_for_remote_cert is not None):
            parametersForEnrollCert.CopyRemoteCertToLocalHost = True
            parametersForEnrollCert.PathForRemoteCertOnLocalHost = opts.path_for_remote_cert
        else:
            if opts.copy_remote_cert and (opts.path_for_remote_cert is None):
                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " Please, set path for remote certificates on local host")
        # check required parmeters for --parameters_from_file
##        if opts.parameters_from_file and (opts.path_of_parameters is not None):
##            parametersForEnrollCert.GetParametersFromFile = True
##            parametersForEnrollCert.PathOfRemoteConnectionparameters = opts.path_of_parameters
##        else:
##            if opts.parameters_from_file and (opts.path_of_parameters is None):
##                sys.exit(bcolors.FAIL + "Error:" + bcolors.ENDC + " Please, set path for parameters")

def EnrollCertificate (HostIp, Port, Username, Password, CaIp, CaCertPath, CertName, Arch):
        if Arch == 64:
            turn_on_gamma_on_crypto_pro = "/opt/cprocsp/sbin/amd64/cpconfig -hardware rndm -add cpsd -name 'CPSD RNG' -level 1"
            add_path1_with_gamma = "/opt/cprocsp/sbin/amd64/cpconfig -hardware rndm -configure cpsd -add string /db1/kis_1 /var/opt/cprocsp/dsrf/db1/kis_1"
            add_path2_with_gamma = "/opt/cprocsp/sbin/amd64/cpconfig -hardware rndm -configure cpsd -add string /db2/kis_1 /var/opt/cprocsp/dsrf/db2/kis_1"
            create_path = "mkdir /usr/local/lib/64"
            create_link = "ln -s /usr/lib/libcurl.so.4.2.0 /usr/local/lib/64/libcurl.so"
            request_and_import_cert = "/opt/cprocsp/bin/amd64/cryptcp -creatcert -dn 'CN=" + str(CertName) + "'" + " -both -km -cont '\\\.\HDIMAGE\\" + str(CertName) + "'" + " -exprt -pin '' -CA 'http://" + str(CaIp) +"/certsrv' -dm -enable-install-root"
            copy_cert_from_container_to_file = "/opt/cprocsp/bin/amd64/cryptcp -CSPcert -km -cont '\\\.\HDIMAGE\\" +str(CertName) + "'" + " -df /root/" + str(CertName) + ".cer -der"
            import_cert_in_sterra_gate_db = "cert_mgr import -f /root/" + str(CertName) + ".cer -kc '\\\.\HDIMAGE\\" + str(CertName) + "'"
            CopyLocalFileToRemoteHost (CaCertPath, '/root/CA.cer', HostIp, Port, Username, Password)
            import_ca_cert_in_sterra_db = "cert_mgr import -f /root/CA.cer -t"
            if parametersForEnrollCert.Verbose:
                print import_ca_cert_in_sterra_db
                print import_cert_in_sterra_gate_db
                print copy_cert_from_container_to_file
                print request_and_import_cert
                print add_path1_with_gamma
                print add_path2_with_gamma
                print turn_on_gamma_on_crypto_pro

            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # create path (fix bug in cryptopro)
            try:
                s.connect(HostIp, Port, Username, Password)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + str(HostIp) + " Connecting or establishing an SSH session failed")
            else:
                stdin, stdout, stderr = s.exec_command(create_path)
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't create path: /usr/local/lib/64 on remote host: " + str(HostIp))
            # create link (fix bug in cryptopro)
            try:
                stdin, stdout, stderr = s.exec_command(create_link)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't create link: \
                ln -s /usr/lib/libcurl.so.4.2.0 /usr/local/lib/64/libcurl.so on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't create link: \
                    ln -s /usr/lib/libcurl.so.4.2.0 /usr/local/lib/64/libcurl.so on remote host: " + str(HostIp))
            # add gamma for cryptopro
            try:
                stdin, stdout, stderr = s.exec_command(turn_on_gamma_on_crypto_pro)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't add CPSD RNG on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't add CPSD RNG on remote host: " + str(HostIp))
            # add path1 for gamma
            try:
                stdin, stdout, stderr = s.exec_command(add_path1_with_gamma)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't add path /var/opt/cprocsp/dsrf/db1/kis_1 on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't add path /var/opt/cprocsp/dsrf/db1/kis_1 on remote host: " + str(HostIp))
            # add path2 for gamma
            try:
                stdin, stdout, stderr = s.exec_command(add_path2_with_gamma)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't add path /var/opt/cprocsp/dsrf/db2/kis_1 on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't add path /var/opt/cprocsp/dsrf/db2/kis_1 on remote host: " + str(HostIp))

            # create request and enroll Gateway certificate from CA
            try:
                stdin, stdout, stderr = s.exec_command(request_and_import_cert)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't create certificate on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't create certificate on remote host: " + str(HostIp))
            # get certificate as file
            try:
                stdin, stdout, stderr = s.exec_command(copy_cert_from_container_to_file)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't copy certificate from container to file on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't copy certificate from container to file on remote host: " + str(HostIp))
            # import Gateway certificate to DB
            try:
                stdin, stdout, stderr = s.exec_command(import_cert_in_sterra_gate_db)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't import Host certificate in S-Terra DB on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't import Host certificate in S-Terra DB on remote host: " + str(HostIp))
            # copy CA certificate to Gateway
            CopyLocalFileToRemoteHost (CaCertPath, '/root/root_ca_s-terra.cer', HostIp, Port, Username, Password)
            # import CA certificate to DB
            try:
                stdin, stdout, stderr = s.exec_command(import_ca_cert_in_sterra_db)
            except:
                sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't import CA certificate in S-Terra DB on remote host: " + str(HostIp))
            else:
                status = stdout.channel.recv_exit_status()
                if status != 0:
                    s.close()
                    sys.exit(bcolors.FAIL + "[Error in EnrollCertificate]: " + bcolors.ENDC + " Can't import CA certificate in S-Terra DB on remote host: " + str(HostIp))
            # close ssh session
            s.close()


def GetFilesFromRemoteHost (IP, Port, Username, Password, LocalPath, RemotePath):
    paramiko.util.log_to_file('paramiko.log')
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        s.connect(IP, Port, Username, Password)
    except:
        sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + str(IP) + " Connecting or establishing an SSH session failed")
    else:
        sftp = s.open_sftp()
        try:
            sftp.stat(RemotePath)
        except IOError:
            s.close()
            sys.exit(bcolors.FAIL + "Error: " + bcolors.ENDC + " File: " + str(RemotePath) + " does't exist on remote host: " +str(IP))
        else:
            sftp.get(RemotePath, LocalPath)
        finally:
            s.close()

def CopyLocalFileToRemoteHost (LocalPath, RemotePath, IP, Port, Username, Password):
    if os.path.isfile(LocalPath): # check to exitst of local file
        try:
            paramiko.util.log_to_file('paramiko.log')
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(IP, Port, Username, Password)
        except:
            sys.exit(bcolors.FAIL + "[Error in CopyLocalFileToRemoteHost]: " + bcolors.ENDC + str(IP) + " Connecting or establishing an SSH session failed")
        else:
            sftp = s.open_sftp()
            try:
                sftp.stat(RemotePath)
            except IOError:
                try:
                    sftp.put(LocalPath, RemotePath) # if file does't exist on remote host copy local file to remote host
                except IOError:
                    sys.exit(bcolors.FAIL + "[Error in CopyLocalFileToRemoteHost]: " + bcolors.ENDC + " Can't copy file: " + str(LocalPath) + " to remote host: " + str(IP))
            else:
                sys.exit(bcolors.FAIL + "[Warning in CopyLocalFileToRemoteHost]: " + bcolors.ENDC + " File already exist: " + str(RemotePath) + " on remote host: " + str(IP))
        finally:
            s.close()
    else:
        sys.exit(bcolors.FAIL + "[Error in CopyLocalFileToRemoteHost]: " + bcolors.ENDC + " file: " + str(LocalPath) + " doesn't exist")

def CopyGammaToRemoteHost ():
    CopyLocalFileToRemoteHost (parametersForEnrollCert.PathOfGamma, parametersForEnrollCert.Path1OfGammaOnRemoteHost, parametersForEnrollCert.IpOfRemoteHost, \
     22, parametersForEnrollCert.SshUsernameForRemoteHost, parametersForEnrollCert.SshPassForRemoteHost)
    CopyLocalFileToRemoteHost (parametersForEnrollCert.PathOfGamma, parametersForEnrollCert.Path2OfGammaOnRemoteHost, parametersForEnrollCert.IpOfRemoteHost, \
     22, parametersForEnrollCert.SshUsernameForRemoteHost, parametersForEnrollCert.SshPassForRemoteHost)
print bcolors.OKGREEN + "[Info]: " + bcolors.ENDC + " Creating the certificate, please wait..."
ParsingparametersOfScript ()
CopyGammaToRemoteHost ()
EnrollCertificate (parametersForEnrollCert.IpOfRemoteHost, 22, parametersForEnrollCert.SshUsernameForRemoteHost, parametersForEnrollCert.SshPassForRemoteHost, \
parametersForEnrollCert.IpOfMsCa, parametersForEnrollCert.PathOfCaCert, parametersForEnrollCert.NameOfCertAndContainer, parametersForEnrollCert.ArchOfRemoteHost)
print bcolors.OKGREEN + "[Info]: " + bcolors.ENDC + " Certificate was successful create ... OK!"

