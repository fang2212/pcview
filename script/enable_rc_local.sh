
# add rc-local to systemd
sudo sh -c "echo '
[Unit]
Description=/etc/rc.local Compatibility
ConditionPathExists=/etc/rc.local

[Service]
Type=forking
ExecStart=/etc/rc.local start
TimeoutSec=0
StandardOutput=tty
RemainAfterExit=yes
SysVStartPriority=99

[Install]
WantedBy=multi-user.target
' > /etc/systemd/system/rc-local.service"

# add rc.local script
sudo sh -c 'echo "#!/bin/sh -e" > /etc/rc.local'
sudo sh -c "echo '
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.
sleep 15
#service cve start
' >> /etc/rc.local"

sudo chmod +x /etc/rc.local

sudo systemctl enable rc-local