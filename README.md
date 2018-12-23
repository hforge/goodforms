GoodForms is a community-driven free software solution to easily generate and work with complex online forms.


Dependencies
=====================

  - itools (master)
  - ikaaro (master)
  - lpod-python (master)

Installation from shell
=================================

Install dependencies
----------------------------

Install itools & ikaaro:

    $ pip install git+https://github.com/hforge/itools.git@master#egg=itools
    $ pip install git+https://github.com/hforge/ikaaro.git@master#egg=ikaaro


1) Install from PIP:
-------------------------

Install from PIP via the command:

    $ pip install git+https://github.com/hforge/goodforms.git@master#egg=goodforms


2) Install from GIT
----------------------------

Install via git repository:

    $ git clone https://github.com/hforge/goodforms/
    $ cd goodforms/
    $ python setup.py -r requirements.txt
    $ python setup.py install


Initialize instance:

    $ icms-init.py -w yourpassword -e email@example.com www.goodforms.localhost

Start instance:

    $ icms-start.py www.goodforms.localhost

Test GoodForms in Firefox:

    $ firefox http://localhost:8080/


Launch via Docker
============================

Build docker image "goodforms":

    $ cd docker
    $ docker build . -t goodforms:latest

Launch demo instance with docker-compose:

    $ cd docker
    $ docker-compose up -d
    $ firefox http://localhost:8080

The login/password is contact@example.com/password !
