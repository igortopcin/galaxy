#!/usr/bin/env bash

# Add neurodebian packages to apt-get
wget -O- http://neuro.debian.net/lists/trusty.us-ca.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
apt-key adv --recv-keys --keyserver hkp://pgp.mit.edu:80 2649A5A9

# Add condor repository to apt sources
if ! grep -q "htcondor" /etc/apt/sources.list; then
cat <<EOF >> /etc/apt/sources.list
deb [arch=amd64] http://research.cs.wisc.edu/htcondor/debian/development/ wheezy contrib
deb [arch=amd64] http://research.cs.wisc.edu/htcondor/debian/stable/ wheezy contrib
EOF
fi

# Get GPG key for condor's repo
wget -qO - http://research.cs.wisc.edu/htcondor/debian/HTCondor-Release.gpg.key | sudo apt-key add -

# Update and install necessary apt-get packages
apt-get update

# Python pip and virtualenv, necessary to develop and run MIGalaxy
apt-get install -y python-pip
apt-get install -y python-virtualenv

# Update python setuptools from source
wget https://bitbucket.org/pypa/setuptools/downloads/ez_setup.py -O - | python

# PostgreSQL database, needed by MIGalaxy
apt-get install -y postgresql-9.3

printf '\n\n' | sudo -u postgres createuser -P vagrant
sudo -u postgres createdb -O vagrant galaxy

# Neurodebian packages, that will be used by tools.
# TODO: this should be replaced by tool-shed deps install procedure.
apt-get install -y mricron
apt-get install -y fsl-core
apt-get install -y afni

# Must source afni.sh and fsl.sh (if they are not already being sourced by bashrc)
if ! grep -q "afni.sh" /etc/bash.bashrc; then
cat <<EOF >> /etc/bash.bashrc

source /etc/afni/afni.sh
source /etc/fsl/fsl.sh

EOF
fi

# Get condor
apt-get install -y condor

# Configure condor submitter and restart it
cp /vagrant/scripts/vagrant/galaxy/condor_config.local /etc/condor/condor_config.local
service condor restart

# Prepare MIGalaxy environment and required directories
rm -f /opt/migalaxy
ln -fs /vagrant /opt/migalaxy

mkdir -p /opt/migalaxy/database/tmp
chown vagrant:vagrant /opt/migalaxy/database/tmp

rm -rf /opt/.venv
mkdir /opt/.venv
chown vagrant:vagrant /opt/.venv

mkdir -p /opt/migalaxy/database/condor
chown vagrant:vagrant /opt/migalaxy/database/condor

# 1. Prepare the virtualenv in which MIGalaxy will run
# 2. Get or scramble the required python eggs
sudo -u vagrant -i <<EOF
cd /opt
virtualenv --no-site-packages .venv

cd /opt/migalaxy
cp config/galaxy.ini.development config/galaxy.ini
cp config/shed_tool_conf.xml.sample config/shed_tool_conf.xml

. /opt/.venv/bin/activate
pip install ipython
pip install ipdb

./scripts/common_startup.sh
python scripts/scramble.py -c config/galaxy.ini.sample -e pydicom
python scripts/scramble.py -c config/galaxy.ini.sample -e nibabel
EOF
