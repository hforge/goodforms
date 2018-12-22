GoodForms is a community-driven free software solution to easily generate and work with complex online forms.


Dependencies
=====================

  - itools (V 0.78)
  - ikaaro (V 0.78)
  - lpod-python (master)

Installation
=====================

From unix shell
----------------------------

Install via git repository:

  $ python setup.py -r requirements.txt
  $ python setup.py install


Initialize instance:

    $ icms-init.py -w yourpassword -e email@example.com www.goodforms.localhost

Start instance:

    $ icms-start.py www.goodforms.localhost

Test GoodForms in Firefox:

    $ firefox http://localhost:8080/


From docker
----------------------------

Build docker image:

   $ cd docker
   $ docker build . -t goodforms:latest

Launch instance with docker-compose:

   $ cd docker
   $ docker-compose up -d
