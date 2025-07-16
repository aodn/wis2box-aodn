#!/bin/bash
set -e

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
cd /opt
python3 -m venv wis2box
source wis2box/bin/activate
pip install --upgrade pip
pip install --upgrade pyopenssl
pip install urllib3==1.26.0

# Add 'ubuntu' user to docker group (if on Ubuntu AMI)
usermod -aG docker ubuntu
