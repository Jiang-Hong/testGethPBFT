#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import USERNAME, PASSWD, MAXPAYLOAD, SEMAPHORE
import paramiko
import threading
import time
import subprocess
import os


class IP(object):
    """
    Create an IP object from a server with a list of rpc ports and a list of listener ports.
    """

    def __init__(self, ip_address, current_port=0, username=USERNAME, password=PASSWD):
        if len(ip_address.split('.')) < 4:
            print("ip is", ip_address)
            raise ValueError('format of ip is not correct')

        self.max_payload = MAXPAYLOAD
        self.current_port = current_port
        self.address = ip_address
        self.rpc_ports = range(8515, 8515 + self.max_payload * 10, 10)
        self.ethereum_network_ports = range(30313, 30313 + self.max_payload * 10, 10)
        self.username = username
        self.password = password

    def __repr__(self):
        return self.address

    def get_new_port(self):
        """Return a tuple from a remote server:(ip_address, rpc_port, ethereum_network_port)."""
        if self.current_port >= self.max_payload:
            raise ValueError("over load")
        result = (self.rpc_ports[self.current_port], self.ethereum_network_ports[self.current_port])
        self.current_port += 1
        return result

    def get_max_payload(self):
        """Return the maximum containers able to run on the server."""
        return self.max_payload

    def is_full_loaded(self):
        """Decide whether the server is full loaded."""
        return self.current_port >= self.max_payload

    def release_ports(self):
        self.current_port = 0

    def exec_command(self, cmd, port=22):
        """
        Exec a command on remote server using SSH connection.
        """
        with SEMAPHORE:
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.address, port, self.username, self.password)
                # time.sleep(0.2)
                stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                # time.sleep(0.1)
                out = stdout.read().strip().decode(encoding='utf-8')
                err = stderr.read().strip().decode(encoding='utf-8')
        if not err:
            result = out
            return result
        else:
            result = err
            if result:
                print('-------------')
                print(cmd)
                print(result)
                print('-------------')
                raise RuntimeError("exec command error: %s" % cmd)

    def is_docker_running(self):
        """Check if docker service is running on specified ip."""
        command = 'systemctl is-active docker'
        result = self.exec_command(command)
        return True if result == 'active' else False

    def stop_containers(self):
        """Stop all containers on the server."""
        get_names_command = "docker ps --format '{{.Names}}'"
        result = self.exec_command(get_names_command).split()
        print('-----------')
        print(' '.join(result))
        stop_all_containers_command = 'docker stop %s' % ' '.join(result)
        self.exec_command(stop_all_containers_command)
        print("all nodes at %s stopped" % self.address)
        print('-----------')

    def remove_containers(self):
        """Remove all containers on the server."""
        get_names_command = "docker ps -a --format '{{.Names}}'"
        result = self.exec_command(get_names_command).split()
        print('-----------')
        print(' '.join(result))
        stop_all_containers_command = 'docker rm %s' % ' '.join(result)
        self.exec_command(stop_all_containers_command)
        print("all nodes at %s removed" % self.address)
        print('-----------')

    def reboot_server(self):
        """Reboot remote server with SSH connection."""
        ssh_reboot_command = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo reboot' % (
            self.password, self.password, self.username, self.address)
        print("server %s reboot" % self.address)
        subprocess.run(ssh_reboot_command, stdout=subprocess.PIPE, shell=True)

    def shutdown_server(self):
        """Shutdown remote server with SSH connection."""
        ssh_shutdown_command = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (
            self.password, self.password, self.username, self.address)
        print("server %s shutdown" % self.address)
        time.sleep(0.02)
        subprocess.run(ssh_shutdown_command, stdout=subprocess.PIPE, shell=True)


class IPList(object):
    """Manage IPs and ports of all servers involved."""

    def __init__(self, ip_file, current_ip=0, username=USERNAME, password=PASSWD):
        """Read IPs from a file."""
        self.current_ip = current_ip
        self.ips = []
        with open(ip_file, 'r') as f:
            for line in f.readlines():
                if line.strip():
                    self.ips.append(IP(line.strip()))
                else:
                    break
        self._init_service()

    def get_ips(self):
        """Return an list of IPs."""
        return self.ips

    def get_full_count(self):
        """Return the number of containers when all servers are full loaded."""
        return len(self.ips) * self.ips[0].get_max_payload() if len(self.ips) else 0

    def get_new_port(self):
        """
        Get a new rpc_port and a new ethereum_network_port along with the IP addr of a server.
        Return: (ip_address, rpc_port, ethereum_network_port)
        """
        if self.current_ip >= len(self.ips):
            raise ValueError("server overload")
        rpc_port, ethereum_network_port = self.ips[self.current_ip].get_new_port()
        current_ip = self.ips[self.current_ip]
        if current_ip.is_full_loaded():
            self.current_ip += 1
        return current_ip, rpc_port, ethereum_network_port

    def release_all_ports(self):
        self.current_ip = 0

    def stop_all_containers(self):
        """Stop all containers running on the servers."""
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.stop_containers)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def remove_all_containers(self):
        """Remove all containers running on the servers."""
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.remove_containers)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def _init_service(self):
        """
        Add key to know_hosts file.
        Start docker service on all servers.
        """
        start_time = time.time()
        known_hosts = os.path.expanduser('~/.ssh/known_hosts')
        keys = paramiko.hostkeys.HostKeys(filename=known_hosts)

        # get results from multi-threading
        # def _set_thread_result(IP, results, index):
        #     results[index] = keys.lookup(ip.address)
        def _set_thread_result(ip: IP, results: dict, index: int):
            return results.setdefault(str(index), keys.lookup(ip.address))

        length = len(self.ips)
        threads = []
        results = {}
        for index, ip in enumerate(self.ips):
            # use multi-threading to lookup keys
            t = threading.Thread(target=_set_thread_result, args=(ip, results, str(index)))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # add keys to known_hosts one by one
        for i in range(length):
            if not results.get(str(i)):
                print('%s is not in know_hosts. Adding to known_hosts' % self.ips[i])
                get_key_command = 'ssh-keyscan %s' % self.ips[i].address
                with open(known_hosts, 'a') as outfile:
                    subprocess.run(get_key_command, stdout=outfile, shell=True)

        start_docker_command = 'echo %s | sudo -S systemctl start docker' % PASSWD
        print('starting docker service on all services')
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.exec_command, args=(start_docker_command,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        end_time = time.time()
        print('initService elapsed time: %.3fs' % (end_time - start_time))

    def reboot_servers(self):
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.reboot_server)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def shutdown_servers(self):
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.shutdown_server)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()


def exec_command(cmd, ip_address, port=22, username=USERNAME, password=PASSWD):
    """Exec a command on remote server using SSH connection."""
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, port, username, password)
        time.sleep(0.2)
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        time.sleep(0.1)
        out = stdout.read().strip().decode(encoding='utf-8')
        err = stderr.read().strip().decode(encoding='utf-8')
        if not err:
            result = out
        else:
            result = err
    return result


def shutdown_server(ip_list, username=USERNAME, password=PASSWD):
    """
    Shutdown all server on IPlist.
    Note: Set param shell=True
    """
    for ip in ip_list.ips:
        shutdown_command = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (password, password, username, IP)
        print("server %s shutdown" % ip.address)
        subprocess.run(shutdown_command, stdout=subprocess.PIPE, shell=True)


def set_ulimit(ip_list):
    """Change ulimit value for servers."""
    for ip in ip_list.ips:
        subprocess.run(['sshpass -p %s scp setUlimit.sh %s@%s:' % (ip.password, ip.username, ip.address)],
                       stdout=subprocess.PIPE, shell=True)
        chmod_command = 'sshpass -p %s ssh -tt %s@%s chmod +x setUlimit.sh' % (ip.password, ip.username, ip.address)
        exec_script_command = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo ./setUlimit.sh' % (
            ip.password, ip.password, ip.username, ip.address)
        print('set nopro and nofile')
        subprocess.run(chmod_command, stdout=subprocess.PIPE, shell=True)
        subprocess.run(exec_script_command, stdout=subprocess.PIPE, shell=True)


# def test(IPlist, username=USERNAME, password=PASSWD):
#     for IP in IPlist.ips:
#         subprocess.run('echo $HOME', shell=True)


if __name__ == "__main__":
    f = IPList('ip.txt')
#    for i in range(10):
#        print(f.get_new_port())
#    f.initService()
