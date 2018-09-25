#! /bin/bash

# debian friendly
aptitude install python-virtualenv python-gobject-dev gcc cmake git \
    python-xapian python-magic python2.6-dev python2.6 python-lxml \
    python-xlrd python-xlwt libsoup-gnome2.4-dev libsoup-gnome2.4-1

# libgit 2 from tarball
cd /tmp/
wget --no-check-certificate --user=guest --password=fr33m1nd42 https://filer.itaapy.com/goodforms/libgit2.tar.gz
tar xvzf libgit2.tar.gz ; cd libgit2
mkdir build ; cd build
cmake ..
cmake --build .
cmake --build . --target install
ldconfig

# create user
adduser --disabled-password --home /opt/goodforms goodforms
