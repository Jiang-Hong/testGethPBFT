#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is about manipulation of servers.
# Assume authorized keys and docker service are configured in all the servers.

from chain.const import USERNAME, PASSWD, KEY_FILE, MAXPAYLOAD, IP_CONFIG, SEMAPHORE
import paramiko
import threading
import time
from typing import Any

# TODO use logging
# username & passwd & pkey for Server

KEY: paramiko.rsakey.RSAKey = paramiko.RSAKey.from_private_key_file(KEY_FILE)
# paramiko.util.log_to_file('/tmp/paramiko.log')


class Server(object):
    """
    Create an Server object with a list of rpc ports and a list of listener ports.
    """

    def __init__(self, ip_address: str, current_port: int = 0) -> None:
        if len(ip_address.split('.')) < 4:
            print("ip is", ip_address)
            raise ValueError('format of ip is not correct')

        self.max_payload = MAXPAYLOAD
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

    def is_full_loaded(self) -> bool:
        """Decide whether the server is full loaded."""
        return self.current_port >= self.max_payload

    def release_ports(self) -> None:
        self.current_port = 0

    def exec_command(self, cmd: str, port: int = 22,
                     username: str = USERNAME,
                     pkey: paramiko.rsakey.RSAKey = KEY) -> Any:
        """
        Exec a command on remote server using SSH connection.
        """
        with SEMAPHORE:    # use semaphore to limit the maximum running threads
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.address, port, username=username, pkey=pkey)
                time.sleep(0.01)
                if username != 'root' and cmd.startswith('sudo'):
                    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)  # need to set get_pty=True
                    stdin.write(PASSWD + '\n')    # input password for privilege command
                    stdin.flush()
                elif username == 'root' and cmd.startswith('sudo'):
                    cmd = cmd[5:]
                    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
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
        Transfer files from local to remote server using SFTP.
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
        Transfer files from remote server to local using SFTP.
        """
        with SEMAPHORE:
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.address, port, username=USERNAME, pkey=KEY)
                sftp = client.open_sftp()
                sftp.get(remote_path, local_path)
                sftp.close()

    def is_docker_running(self) -> bool:
        """Check if docker service is running on server."""
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
        if not result:
            return
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
        """Add a mirror for docker images"""
        self.put_file('daemon.json', 'daemon.json')
        self.exec_command('sudo cp daemon.json /etc/docker/daemon.json && sudo systemctl restart docker')

    def set_limits(self) -> None:
        self.put_file('limits.conf', 'limits.conf')
        self.exec_command('sudo cp limits.conf /etc/security/limits.conf')

    def journalctl_vacuum(self) -> None:
        """Removes archived journal files until the disk space they use falls below 10M"""
        self.exec_command('sudo journalctl --vacuum-size=10M')

    def sync_time(self) -> None:
        self.exec_command('sudo apt-get install ntpdate -qqy')
        self.exec_command('sudo ntpdate cn.pool.ntp.org')


class ServerList(object):
    """Manage all servers."""
    def __init__(self, ip_file: str, current_ip: int = 0) -> None:
        """Read servers' IP addresses from a file."""
        self._current_ip = current_ip
        self._available_ip = 0
        self.servers = []
        self.ip_count = 0
        with open(ip_file, 'r') as cfg_file:
            # read servers' IP addresses from a config file
            # stop at empty line
            for line in cfg_file.readlines():
                line = line.strip()
                if line:
                    self.servers.append(Server(line))
                else:
                    break
        self.length = len(self.servers)

    @property
    def current_ip(self) -> int:
        return self._current_ip

    @current_ip.setter
    def current_ip(self, cur: int) -> None:
        self._current_ip = cur
        if self._current_ip >= self.ip_count:  #TODO
            self._current_ip = self._available_ip

    def __getitem__(self, position):
        return self.servers[position]

    def __len__(self):
        return self.length

    def __repr__(self):
        return ', '.join(map(str, self.servers))

    def get_full_count(self) -> int:
        """Return the number of containers when all servers are full loaded."""
        return self.length * self.servers[0].max_payload if self.length else 0

    def get_new_port(self) -> tuple:
        """
        Get a new rpc_port and a new ethereum_network_port along with the IP addr of a server.
        Return: (ip_address, rpc_port, ethereum_network_port)
        """
        if self._available_ip >= self.length:
            raise ValueError("server overload")
        rpc_port, ethereum_network_port = self.servers[self.current_ip].get_new_port()
        tmp_ip = self.servers[self.current_ip]
        if tmp_ip.is_full_loaded():
            self._available_ip = self.current_ip + 1
        self._current_ip += 1
        if self._current_ip >= self.length:
            self._current_ip = self._available_ip
        return tmp_ip, rpc_port, ethereum_network_port

    def release_all_ports(self) -> None:
        for server in self.servers:
            server.current_port = 0
        self.current_ip = 0

    def exec_commands(self, cmd: str, port: int = 22) -> None:
        """Exec an uniform command on all servers"""
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.exec_command, args=(cmd,), kwargs={'port': port})
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def async_exec_commands(self, cmd:str, port: int = 22) -> None:
        """Async version of exec_commands"""
        pass

    def put_files(self, local_path: str, remote_path: str, port: int = 22) -> None:
        """Transfer files from local to remote servers using SFTP."""
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.put_file, args=(local_path, remote_path), kwargs={'port': port})
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def get_files(self, remote_path: str, local_path: str, port: int = 22) -> None:
        """Transfer files from remote servers to local using SFTP."""
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.get_file, args=(remote_path, local_path), kwargs={'port': port})
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def stop_all_containers(self) -> None:
        """Stop all containers running on the servers."""
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.stop_containers)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def remove_all_containers(self) -> None:
        """Remove all containers running on the servers."""
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.remove_containers)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def start_docker_service(self) -> None:
        """
        # Add key to know_hosts file &&
        start docker service on all servers.
        """
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
        # self.ip_count = self.length
        # threads = []
        # results = {}
        # for index, ip in enumerate(self.servers):
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
        # #         print('%s is not in know_hosts. Adding to known_hosts.' % self.servers[i])
        # #         get_key_command = 'ssh-keyscan %s' % self.servers[i].address
        # #         with open(known_hosts, 'a') as outfile:
        # #             subprocess.run(get_key_command, stdout=outfile, shell=True)
        #
        # # start_docker_command = 'echo %s | sudo -S systemctl start docker' % PASSWD
        # """
        start_docker_command = 'sudo systemctl start docker'
        print('starting docker service on all services')
        self.exec_commands(start_docker_command)

    def reboot_servers(self) -> None:  # TODO use asyncio
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.reboot_server)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def shutdown_servers(self) -> None:
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.shutdown_server)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def mirror(self) -> None:
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.mirror)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def set_limits(self) -> None:
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.set_limits)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def journalctl_vacuum(self) -> None:
        """Removes archived journal files until the disk space they use falls below 10M"""
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.journalctl_vacuum)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def sync_time(self) -> None:
        threads = []
        for ip in self.servers:
            t = threading.Thread(target=ip.sync_time)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()


if __name__ == "__main__":
    servers = ServerList(ip_file=IP_CONFIG)
    # ip_list.init_service()
    # ip_list.stop_all_containers()
