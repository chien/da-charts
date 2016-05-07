#!/usr/bin/env bash

fail() {
    echo $1 && exit 1
}

VUSER='sudo -u vagrant -H'
PUSER='sudo -u postgres -H'

# Create Swap File for pandas lib building in case of VM memory shortage
sudo dd if=/dev/zero of=/swapfile bs=1024 count=524288
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

apt-get update
apt-get install -y traceroute git-core python-dev build-essential python-software-properties python3-pip postgresql-9.3 postgresql-contrib-9.3 python-psycopg2 libpq-dev python-setuptools rabbitmq-server libffi-dev python-openssl
apt-get install -y nodejs npm
npm install -g bower

$PUSER psql -c "create user vagrant superuser"
$PUSER psql -U postgres -d postgres -c "alter user vagrant with password 'password';"
$PUSER createdb -O vagrant retsku_development

ROOT=/vagrant

# Install Python VirtualEnv
pip3 install virtualenv
if [ ! -d $ROOT/.env ]; then
    virtualenv -p python3 $ROOT/.env || fail "Failed to create virtualenv!"
fi
. $ROOT/.env/bin/activate || fail "Failed to activate virtualenv!"

# due to bug in numpy install pandas and numpy using pip - https://github.com/numpy/numpy/issues/2434
pip3 install -r $ROOT/requirements.txt

echo "source /vagrant/.env/bin/activate" >> /home/vagrant/.bashrc

local_ip=`traceroute -n 8.8.8.8 | tail -n+2 | awk '{ print $2 }' | head -1`
echo "$local_ip myapp.dev" >> /etc/hosts
