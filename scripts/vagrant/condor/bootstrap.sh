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

# Neurodebian packages, that will be used by tools.
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

# Configure condor central manager and restart it
cp /vagrant/scripts/vagrant/condor/condor_config.local /etc/condor/condor_config.local
service condor restart

rm -f /opt/migalaxy
ln -fs /vagrant /opt/migalaxy

mkdir -p /opt/migalaxy/database/tmp
chown vagrant:vagrant /opt/migalaxy/database/tmp

