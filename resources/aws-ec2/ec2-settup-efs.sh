#!/bin/bash
set -ex

# Prepare for Docker install
mkdir -p /usr/share/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
chmod a+r /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-compose-plugin unzip python3-pip python3.12-venv

# Setup Python virtual environment in /opt/wis2box (or another non-root user's home if desired)
# TODO: remove this code if tests pass, WIS2BOX new version 1.0 does not need a virtual env anymore
# cd /opt
# python3 -m venv wis2box
# source wis2box/bin/activate
# pip install --upgrade pip
# pip install --upgrade pyopenssl
# pip install urllib3==1.26.0

# Add 'ubuntu' user to docker group (if on Ubuntu AMI)
usermod -aG docker ubuntu

# Install EFS Client
apt-get update
apt-get -y install git binutils rustc cargo pkg-config libssl-dev gettext

# Check network connectivity
curl -I https://github.com || { echo "Network error: Cannot reach GitHub"; exit 1; }

cd /opt
git clone https://github.com/aws/efs-utils || { echo "git clone failed"; exit 1; }
cd efs-utils
./build-deb.sh || { echo "efs-utils build failed"; exit 1; }
apt-get -y install ./build/amazon-efs-utils*deb || { echo "efs-utils install failed"; exit 1; }

# Create mount point for EFS
mkdir -p /mnt/efs-mount-point
mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport 10.1.1.32:/ /mnt/efs-mount-point

# Start the WIS2BOX services
cp -r /mnt/efs-mount-point/wis2box /home/ubuntu/wis2box
cd /home/ubuntu/wis2box
python3 wis2box-ctl.py start
