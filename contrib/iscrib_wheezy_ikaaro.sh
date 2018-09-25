#! /bin/bash

GF_ADMIN=nderam@gmail.com
GF_PWD=foobar

# virtualenv
cd /opt/goodforms
# mkdir -p prod ; cd prod
virtualenv --system-site-packages -p /usr/bin/python2.6 gip-goodforms_prod ; cd gip-goodforms_prod

# pip install
./bin/pip install pytz

# get template
wget --no-check-certificate --user=guest --password=fr33m1nd42 https://github.com/hforge/goodforms/template.tar.gz
tar xvzf template.tar.gz

# remove vt-env libs
rm -fr template/lib/python2.6/site-packages/pip-0.7.2-py2.6.egg/
rm -fr template/lib/python2.6/site-packages/setuptools.pth
rm -fr template/lib/python2.6/site-packages/easy-install.pth
rm -fr template/lib/python2.6/site-packages/distribute-0.6.10-py2.6.egg/

# copy bins
for i in `ls bin`; do rm template/bin/$i; done
cp template/bin/* bin/

# copy libs
cp -r template/lib/python2.6/site-packages/* lib/python2.6/site-packages/

# dumb fix... utf8
sed -i 's/^# Copyright.*//g' /opt/goodforms/gip-goodforms_prod/lib/python2.6/site-packages/itools/pdf/css.py


# instance
rm -f ~/.gitconfig
git config --global --add user.email $GF_ADMIN
git config --global --add user.name $GF_ADMIN
./bin/icms-init.py -p 8080 -e $GF_ADMIN -w $GF_PWD -r goodforms goodforms.instance
