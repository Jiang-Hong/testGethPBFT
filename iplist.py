#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is about manipulation of servers.

from const import USERNAME, PASSWD, KEY_FILE, MAXPAYLOAD, IP_CONFIG, SEMAPHORE
import paramiko
import threading
import time
import os
from typing import Any

KEY: paramiko.rsakey.RSAKey = paramiko.RSAKey.from_private_key_file(KEY_FILE)
# paramiko.util.log_to_file('/tmp/paramiko.log')


class IP(object):
    """
    Create an IP object with a list of rpc ports and a list of listener ports.
    """

    def __init__(self, ip_address: str, current_port: int = 0) -> None:
        if len(ip_address.split('.')) < 4:
            print("ip is", ip_address)
            raise ValueError('format of ip is not correct')

        self._max_payload = MAXPAYLOAD
        self.current_port = current_port
        self.address = ip_address
        self.rpc_ports = range(8515, 8515 + self.max_payload * 10, 10)
        self.ethereum_network_ports = range(30313, 30313 + self.max_payload * 10, 10)

    def __repr__(self) -> str:
        return self.address

    def get_new_port(self) -> tuple:
        """Return a tuple from a remote server:(ip_address, rpc_port, ethereum_network_port)."""
        if self.current_port >= self.max_payload:
            raise ValueError("over load")
        result = (self.rpc_ports[self.current_port], self.ethereum_network_ports[self.current_port])
        self.current_port += 1
        return result

    @property
    def max_payload(self) -> int:
        """Return the maximum containers able to run on the server."""
        return self._max_payload

    @max_payload.setter
    def max_payload(self, payload: int) -> None:
        """Set maximum payload value."""
        print("set new maximum payload for %s" % self.address)
        self._max_payload = payload

    def is_full_loaded(self) -> bool:
        """Decide whether the server is full loaded."""
        return self.current_port >= self.max_payload

    def release_ports(self) -> None:
        self.current_port = 0

    def exec_command(self, cmd: str, port: int = 22) -> Any:
        """
        Exec a command on remote server using SSH connection.
        """
        with SEMAPHORE:    # use semaphore to limit the maximum running threads
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.address, port, username=USERNAME, pkey=KEY)
                if USERNAME != 'root' and cmd.startswith('sudo'):
                    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                    stdin.write(PASSWD + '\n')
                    stdin.flush()
                else:
                    stdin, stdout, stderr = client.exec_command(cmd)
                out = stdout.read().strip().decode(encoding='utf-8')
                err = stderr.read().strip().decode(encoding='utf-8')
        if not err:
            result = out.strip()
            if result:
                print(result)
            return result
        else:
            result = err
            if result:
                print('-------------')
                print(self.address, cmd)
                print(result)
                print('-------------')
                raise RuntimeError("exec command error: %s" % cmd)

    def put_file(self, local_path: str, remote_path: str, port: int = 22) -> None:
        """
        Transfer files from local to remote server using sftp.
        """
        with SEMAPHORE:
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.address, port, username=USERNAME, pkey=KEY)
                sftp = client.open_sftp()
                sftp.put(local_path, remote_path)
                sftp.close()

    def get_file(self, remote_path: str, local_path: str, port: int = 22) -> None:
        """
        Transfer files from remote server to local using sftp.
        """
        with SEMAPHORE:
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.address, port, username=USERNAME, pkey=KEY)
                sftp = client.open_sftp()
                sftp.get(remote_path, local_path)
                sftp.close()

    def is_docker_running(self) -> bool:
        """Check if docker service is running on specified ip."""
        command = 'hostname -I && systemctl is-active docker'
        result = self.exec_command(command)
        return True if result.split()[-1] == 'active' else False

    def stop_containers(self) -> None:
        """Stop all containers on the server."""
        get_names_command = "docker ps --format '{{.Names}}'"
        result = self.exec_command(get_names_command).split()
        if not result:
            return
        print('-----------')
        stop_all_containers_command = 'docker stop %s' % ' '.join(result)
        self.exec_command(stop_all_containers_command)
        print("all nodes at %s stopped" % self.address)
        print('-----------')

    def remove_containers(self) -> None:
        """Remove all containers on the server."""
        get_names_command = "docker ps -a --format '{{.Names}}'"
        result = self.exec_command(get_names_command).split()
        print('--removing nodes--')
        stop_all_containers_command = 'docker rm %s' % ' '.join(result)
        self.exec_command(stop_all_containers_command)
        print("all nodes at %s removed" % self.address)
        print('---removed---')

    def reboot_server(self) -> None:
        """Reboot remote server."""
        self.exec_command('sudo reboot')

    def shutdown_server(self) -> None:
        """Shutdown remote server."""
        self.exec_command('sudo shutdown now')
        # # -*- alternative approach -*-
        # ssh_shutdown_command = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (
        #     self.password, self.password, self.username, self.address)
        # print("server %s shutdown" % self.address)
        # time.sleep(0.02)
        # subprocess.run(ssh_shutdown_command, stdout=subprocess.PIPE, shell=True)  # necessary to set shell param True

    def mirror(self) -> None:
        self.put_file('daemon.json', 'daemon.json')
        self.exec_command('sudo cp daemon.json /etc/docker/daemon.json && sudo systemctl restart docker')

    def set_limits(self) -> None:
        self.put_file('limits.conf', 'limits.conf')
        self.exec_command('sudo cp limits.conf /etc/security/limits.conf')
        # # -*- alternative approach -*-
        # set_limits_cmd = 'sshpass -p %s scp limits.conf %s@%s:limits.conf' % (
        #     self.password, self.username, self.address)
        # time.sleep(0.02)
        # subprocess.run(set_limits_cmd, stdout=subprocess.PIPE, shell=True)
        # cp_cmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo cp limits.conf /etc/security/limits.conf' % (
        #     self.password, self.password, self.username, self.address)
        # subprocess.run(cp_cmd, stdout=subprocess.PIPE, shell=True)

    def journalctl_vacuum(self) -> None:
        self.exec_command('sudo journalctl --vacuum-size=10M')


class IPList(object):
    """Manage IPs and ports of all servers involved."""

    def __init__(self, ip_file: str, current_ip: int = 0) -> None:
        """Read IPs from a file."""
        self._current_ip = current_ip
        self._available_ip = 0
        self._ips = []
        self.ip_count = 0
        with open(ip_file, 'r') as file:
            # read servers' IPs from an IP config file
            # stop at empty line
            for line in file.readlines():
                if line.strip():
                    self.ips.append(IP(line.strip()))
                else:
                    break
        self._init_service()

    @property
    def ips(self) -> [IP]:
        """Return a list of IPs."""
        return self._ips

    @property
    def current_ip(self) -> int:
        return self._current_ip

    @current_ip.setter
    def current_ip(self, cur: int) -> None:
        self._current_ip = cur
        if self._current_ip >= self.ip_count:  #TODO
            self._current_ip = self._available_ip

    def get_full_count(self) -> int:
        """Return the number of containers when all servers are full loaded."""
        return len(self.ips) * self.ips[0].max_payload if len(self.ips) else 0

    def get_new_port(self) -> tuple:
        """
        Get a new rpc_port and a new ethereum_network_port along with the IP addr of a server.
        Return: (ip_address, rpc_port, ethereum_network_port)
        """
        if self._available_ip >= len(self.ips):
            raise ValueError("server overload")
        rpc_port, ethereum_network_port = self.ips[self.current_ip].get_new_port()
        tmp_ip = self.ips[self.current_ip]
        if tmp_ip.is_full_loaded():
            self._available_ip = self.current_ip + 1
        self._current_ip += 1
        if self._current_ip >= len(self.ips):
            self._current_ip = self._available_ip
        return tmp_ip, rpc_port, ethereum_network_port

    def release_all_ports(self) -> None:
        for ip in self.ips:
            ip.current_port = 0
        self.current_ip = 0

    def exec_commands(self, cmd: str, port: int = 22) -> None:
        """Exec an uniform command on all servers"""
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.exec_command, args=(cmd,), kwargs={'port': port})
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def stop_all_containers(self) -> None:
        """Stop all containers running on the servers."""
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.stop_containers)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def remove_all_containers(self) -> None:
        """Remove all containers running on the servers."""
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.remove_containers)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def _init_service(self) -> None:
        """
        # Add key to know_hosts file &&
        start docker service on all servers.
        """

        start_time = time.time()
        # """
        # known_hosts = os.path.expanduser('~/.ssh/known_hosts')
        # keys = paramiko.hostkeys.HostKeys(filename=known_hosts)
        #
        # # get results from multi-threading
        # # def _set_thread_result(IP, results, index):
        # #     results[index] = keys.lookup(ip.address)
        # def _set_thread_result(ip: IP, results: dict, index: int) -> None:
        #     return results.setdefault(str(index), keys.lookup(ip.address))
        #
        # self.ip_count = len(self.ips)
        # threads = []
        # results = {}
        # for index, ip in enumerate(self.ips):
        #     # use multi-threading to lookup keys
        #     t = threading.Thread(target=_set_thread_result, args=(ip, results, str(index)))
        #     t.start()
        #     threads.append(t)
        # for t in threads:
        #     t.join()
        #
        # # add keys to known_hosts one by one
        # # for i in range(self.ip_count):
        # #     if not results.get(str(i)):
        # #         print('%s is not in know_hosts. Adding to known_hosts.' % self.ips[i])
        # #         get_key_command = 'ssh-keyscan %s' % self.ips[i].address
        # #         with open(known_hosts, 'a') as outfile:
        # #             subprocess.run(get_key_command, stdout=outfile, shell=True)
        #
        # # start_docker_command = 'echo %s | sudo -S systemctl start docker' % PASSWD
        # """
        start_docker_command = 'sudo systemctl start docker'
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

    def reboot_servers(self) -> None:
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.reboot_server)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def shutdown_servers(self) -> None:
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.shutdown_server)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def restart_network(self) -> None:
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.restart_network)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def mirror(self) -> None:
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.mirror)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def set_limits(self) -> None:
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.set_limits)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def journalctl_vacuum(self) -> None:
        threads = []
        for ip in self.ips:
            t = threading.Thread(target=ip.journalctl_vacuum)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()


def exec_command(cmd, ip_address: str, port: int = 22,
                 username: str = USERNAME, password: str = PASSWD) -> Any:
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
            print(result)
        else:
            result = err
    return result


def shutdown_server(ip_list: IPList, username: str = USERNAME, password: str = PASSWD) -> None:
    """
    Shutdown all server on IPlist.
    Note: Set param shell=True
    """
    for ip in ip_list.ips:
        ip.shutdown_server()
        # shutdown_command = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' \
        #                    % (password, password, username, IP)
        # print("server %s shutdown" % ip.address)
        # subprocess.run(shutdown_command, stdout=subprocess.PIPE, shell=True)


# def set_ulimit(ip_list: IPList) -> None:
#     """Change ulimit for servers."""
#     for ip in ip_list.ips:
#         subprocess.run(['sshpass -p %s scp setUlimit.sh %s@%s:' % (ip.password, ip.username, ip.address)],
#                        stdout=subprocess.PIPE, shell=True)
#         chmod_command = 'sshpass -p %s ssh -tt %s@%s chmod +x setUlimit.sh' % (ip.password, ip.username, ip.address)
#         exec_script_command = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo ./setUlimit.sh' % (
#             ip.password, ip.password, ip.username, ip.address)
#         print('set noproc and nofile')
#         subprocess.run(chmod_command, stdout=subprocess.PIPE, shell=True)
#         subprocess.run(exec_script_command, stdout=subprocess.PIPE, shell=True)


# def test(IPlist, username=USERNAME, password=PASSWD):
#     for IP in IPlist.ips:
#         subprocess.run('echo $HOME', shell=True)


if __name__ == "__main__":
    f = IPList(IP_CONFIG)
    f.stop_all_containers()
    # f.stop_all_containers()
    # time.sleep(0.2)
    # f.remove_all_containers()
    # TODO 2. use Logging module
    # TODO 1. multiprocessing? partly
