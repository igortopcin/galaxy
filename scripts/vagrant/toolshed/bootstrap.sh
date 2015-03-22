#!/usr/bin/env bash

# Update and install necessary apt-get packages
apt-get update

# Python pip and virtualenv, necessary to develop and run MIGalaxy
apt-get install -y python-pip
apt-get install -y python-virtualenv
apt-get install -y curl

# Update python setuptools from source
#wget https://bitbucket.org/pypa/setuptools/downloads/ez_setup.py -O - | python

# PostgreSQL database, needed by MIGalaxy
#apt-get install -y postgresql-9.3

#printf '\n\n' | sudo -u postgres createuser -P vagrant
#sudo -u postgres createdb -O vagrant toolshed

# Prepare MIGalaxy environment and required directories
rm -f /opt/toolshed
ln -fs /vagrant /opt/toolshed

rm -rf /opt/database
mkdir /opt/database
mkdir /opt/database/tmp
mkdir /opt/database/community_files
mkdir /opt/database/beaker_sessions
chown -R vagrant:vagrant /opt/database

rm -rf /opt/.venv
mkdir /opt/.venv
chown vagrant:vagrant /opt/.venv

# 1. Prepare the virtualenv in which MIGalaxy will run
# 2. Bootstrap toolshed
sudo -u vagrant -i <<EOF
cd /opt
virtualenv --no-site-packages .venv

cd /opt/toolshed
cp config/tool_shed.ini.development config/tool_shed.ini
TOOL_SHED_CONFIG_FILE=./config/tool_shed.ini sh run_tool_shed.sh -bootstrap_from_tool_shed http://toolshed.g2.bx.psu.edu
EOF
