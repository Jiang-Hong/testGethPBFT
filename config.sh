
echo dell@2017 | sudo -S apt-get install docker.io openssh-server sshpass
echo dell@2017 | sudo -S usermod -aG docker dell
echo dell@2017 | sudo -S echo "MaxSessions 3000" >> /etc/ssh/sshd_config
echo dell@2017 | sudo -S echo "MaxStartups 1000:30:2000" >> /etc/ssh/sshd_config