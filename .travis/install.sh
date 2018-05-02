#!/bin/bash -uex

cat << EOR | sudo tee -a /etc/os-release
NAME="Ubuntu"
VERSION="14.04.2 LTS, Trusty Tahr"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 14.04.2 LTS"
VERSION_ID="14.04"
HOME_URL="http://www.ubuntu.com/"
EOR

if [[ $JUJU_VERSION == 2 ]]; then
    sudo add-apt-repository -y ppa:juju/stable
    JUJU_PKGS="juju lxd"
else
    sudo add-apt-repository -y ppa:juju/1.25
    JUJU_PKGS="juju juju-local"
fi

sudo apt-get update
sudo apt-get install -t trusty-backports -y bzr $JUJU_PKGS

if [[ $JUJU_VERSION == 2 ]]; then
    echo User: $USER
    sudo usermod -a -G lxd $USER
    sudo lxd init --auto
fi
